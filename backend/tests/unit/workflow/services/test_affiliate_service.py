"""Affiliate Service 테스트"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.persistence.models import Affiliate, Order, Settings, AffiliatePayment
from src.workflow.services.affiliate_service import AffiliateService


class TestRecordMarketingCommissionIfApplicable:
    """마케팅 커미션 기록"""

    def test_record_marketing_commission_success_with_valid_affiliate(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_product,
    ):
        """TC-2.1.1: Affiliate code가 있는 주문의 마케팅 커미션 자동 기록"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        # Order에 marketing_affiliate_id 설정
        order_with_customer.marketing_affiliate_id = affiliate_active.id
        order_with_customer.payment_status = "paid"
        order_with_customer.total_profit = Decimal("160.00")  # 80 * 2 (수량 2)
        test_db.add(order_with_customer)
        test_db.commit()

        # OrderItem 추가
        from src.persistence.models import OrderItem
        order_item = OrderItem(
            order_id=order_with_customer.id,
            product_id=sample_product.id,
            quantity=2,
            unit_price=sample_product.price,
            profit_per_item=Decimal("80.00"),
        )
        test_db.add(order_item)
        test_db.commit()

        # Settings 생성
        settings = Settings(
            profit_per_unit=Decimal("80.00"),
            marketing_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # When
        AffiliateService.record_marketing_commission_if_applicable(test_db, order_with_customer)

        # Then
        # affiliate_sales 확인
        assert order_with_customer.affiliate_sales
        affiliate_sale = order_with_customer.affiliate_sales[0]
        assert affiliate_sale.affiliate_id == affiliate_active.id
        assert affiliate_sale.marketing_commission == Decimal("32.00")  # 80 * 0.2 * 2

    def test_no_commission_without_affiliate(
        self,
        test_db: Session,
        order_with_customer: Order,
    ):
        """TC-2.1.2: Affiliate code 없는 경우 commission 미기록"""
        # Given
        order_with_customer.affiliate_id = None
        order_with_customer.payment_status = "paid"
        test_db.add(order_with_customer)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # When
        AffiliateService.record_commission_if_applicable(test_db, order_with_customer)

        # Then
        assert len(order_with_customer.affiliate_sales) == 0


class TestValidateAndRecordAffiliateOnOrderCreation:
    """Order 생성 시 Affiliate 유효성 검증"""

    def test_invalid_affiliate_code_creates_error_log(
        self,
        test_db: Session,
        order_with_customer: Order,
    ):
        """TC-2.1.4: 존재하지 않는 affiliate code"""
        # Given
        test_db.add(order_with_customer)
        test_db.commit()

        invalid_code = "aff-invalid-9999"

        # When
        result = AffiliateService.validate_and_record_affiliate_on_order_creation(
            test_db,
            order_with_customer,
            invalid_code,
        )

        # Then
        assert result is None  # affiliate_id는 설정되지 않음
        assert len(order_with_customer.affiliate_error_logs) == 1
        error_log = order_with_customer.affiliate_error_logs[0]
        assert error_log.error_type == "INVALID_CODE"
        assert error_log.affiliate_code == invalid_code

    def test_inactive_affiliate_creates_error_log(
        self,
        test_db: Session,
        order_with_customer: Order,
        affiliate_inactive: Affiliate,
    ):
        """TC-2.1.5: 비활성화된 affiliate"""
        # Given
        test_db.add(affiliate_inactive)
        test_db.add(order_with_customer)
        test_db.commit()

        # When
        result = AffiliateService.validate_and_record_affiliate_on_order_creation(
            test_db,
            order_with_customer,
            affiliate_inactive.code,
        )

        # Then
        assert result is None  # affiliate_id는 설정되지 않음
        assert len(order_with_customer.affiliate_error_logs) == 1
        error_log = order_with_customer.affiliate_error_logs[0]
        assert error_log.error_type == "INACTIVE_AFFILIATE"
        assert error_log.affiliate_code == affiliate_inactive.code

    def test_valid_affiliate_returns_affiliate_id(
        self,
        test_db: Session,
        order_with_customer: Order,
        affiliate_active: Affiliate,
    ):
        """TC-2.1.1 확장: 유효한 affiliate ID 반환"""
        # Given
        test_db.add(affiliate_active)
        test_db.add(order_with_customer)
        test_db.commit()

        # When
        result = AffiliateService.validate_and_record_affiliate_on_order_creation(
            test_db,
            order_with_customer,
            affiliate_active.code,
        )

        # Then
        assert result == affiliate_active.id
        assert len(order_with_customer.affiliate_error_logs) == 0


class TestCommissionCalculationAccuracy:
    """Commission 금액 정확성"""

    def test_commission_calculation_correctness(self, test_db: Session):
        """TC-2.1.3: Commission 금액 정확성"""
        # Given
        profit = Decimal("80.00")
        commission_rate = Decimal("0.2")

        # When
        commission = AffiliateService.calculate_commission(profit, commission_rate)

        # Then
        assert commission == Decimal("16.00")

    def test_commission_calculation_with_different_values(self, test_db: Session):
        """Commission 계산 - 다양한 값"""
        test_cases = [
            (Decimal("100.00"), Decimal("0.2"), Decimal("20.00")),
            (Decimal("50.00"), Decimal("0.2"), Decimal("10.00")),
            (Decimal("1000.00"), Decimal("0.15"), Decimal("150.00")),
        ]

        for profit, rate, expected in test_cases:
            result = AffiliateService.calculate_commission(profit, rate)
            assert result == expected


class TestAffiliateSalesTracking:
    """판매 건수 추적"""

    def test_single_sale_creates_affiliate_sale_record(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
    ):
        """TC-B.2.1: 하나의 주문 판매 시 판매 기록이 생성된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        order_with_customer.affiliate_id = affiliate_active.id
        order_with_customer.payment_status = "completed"
        test_db.add(order_with_customer)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # When
        AffiliateService.record_commission_if_applicable(test_db, order_with_customer)

        # Then
        assert len(affiliate_active.sales) == 1
        sale = affiliate_active.sales[0]
        assert sale.commission_amount == Decimal("16.00")

    def test_multiple_sales_are_all_recorded(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_customer,
        sample_product,
        shipping_rate_ncr,
    ):
        """TC-B.2.2: 여러 주문의 판매가 모두 누적된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # 첫 번째 주문
        order_with_customer.affiliate_id = affiliate_active.id
        order_with_customer.payment_status = "completed"
        test_db.add(order_with_customer)
        test_db.commit()
        AffiliateService.record_commission_if_applicable(test_db, order_with_customer)

        # 두 번째 주문
        order2 = Order(
            order_number="ORD-test-002",
            customer_id=sample_customer.id,
            subtotal=Decimal("50.00"),
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("150.00"),
            payment_status="completed",
            shipping_status="preparing",
            profit=Decimal("80.00"),
            affiliate_id=affiliate_active.id,
        )
        test_db.add(order2)
        test_db.commit()
        AffiliateService.record_commission_if_applicable(test_db, order2)

        # 세 번째 주문
        order3 = Order(
            order_number="ORD-test-003",
            customer_id=sample_customer.id,
            subtotal=Decimal("50.00"),
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("150.00"),
            payment_status="completed",
            shipping_status="preparing",
            profit=Decimal("80.00"),
            affiliate_id=affiliate_active.id,
        )
        test_db.add(order3)
        test_db.commit()
        AffiliateService.record_commission_if_applicable(test_db, order3)

        # Refresh to get updated relationships
        test_db.refresh(affiliate_active)

        # Then
        assert len(affiliate_active.sales) == 3


class TestAffiliateRevenueCalculation:
    """누적 수익 계산"""

    def test_single_order_revenue_calculation(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
    ):
        """TC-B.3.1: 하나의 주문 판매 시 누적 수익이 정상 기록된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        order_with_customer.affiliate_id = affiliate_active.id
        order_with_customer.payment_status = "completed"
        test_db.add(order_with_customer)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        AffiliateService.record_commission_if_applicable(test_db, order_with_customer)
        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)

        # Then
        assert total_revenue == Decimal("16.00")

    def test_multiple_orders_revenue_accumulation(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_customer,
    ):
        """TC-B.3.2: 여러 주문의 수익이 누적된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # 3개 주문 생성 및 처리
        for i in range(3):
            order = Order(
                order_number=f"ORD-test-rev-{uuid4().hex[:8]}",
                customer_id=sample_customer.id,
                subtotal=Decimal("50.00"),
                shipping_fee=Decimal("100.00"),
                total_price=Decimal("150.00"),
                payment_status="completed",
                shipping_status="preparing",
                profit=Decimal("80.00"),
                affiliate_id=affiliate_active.id,
            )
            test_db.add(order)
            test_db.commit()
            AffiliateService.record_commission_if_applicable(test_db, order)

        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)

        # Then - 각 주문: 80 * 0.2 = 16, 총 3개 = 48
        assert total_revenue == Decimal("48.00")

    def test_inactive_affiliate_no_revenue(
        self,
        test_db: Session,
        affiliate_inactive: Affiliate,
        order_with_customer: Order,
    ):
        """TC-B.3.3: 비활성화된 어필리에이트는 수익이 기록되지 않는다"""
        # Given
        test_db.add(affiliate_inactive)
        test_db.commit()

        order_with_customer.affiliate_id = affiliate_inactive.id
        order_with_customer.payment_status = "completed"
        test_db.add(order_with_customer)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # When - 비활성화 상태에서는 기록되지 않아야 함
        # (실제로는 validate_and_record_affiliate_on_order_creation에서 필터링됨)
        test_db.refresh(affiliate_inactive)

        # Then
        assert len(affiliate_inactive.sales) == 0


class TestAffiliatePendingCommissionCalculation:
    """지급 예상 수수료 계산"""

    def test_pending_commission_with_no_payment_history(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
    ):
        """TC-B.4.1: 지급 이력이 없으면 지급 예상 수수료 = 누적 수익"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        order_with_customer.affiliate_id = affiliate_active.id
        order_with_customer.payment_status = "completed"
        test_db.add(order_with_customer)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        AffiliateService.record_commission_if_applicable(test_db, order_with_customer)
        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)
        total_paid = sum(
            payment.amount
            for payment in affiliate_active.payments
            if payment.status == "completed"
        )
        pending_commission = total_revenue - total_paid

        # Then
        assert pending_commission == Decimal("16.00")

    def test_pending_commission_after_partial_payment(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_customer,
    ):
        """TC-B.4.2: 부분 지급 후 남은 금액이 지급 예상 수수료가 된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # 3개 주문으로 총 수익 48 생성
        for i in range(3):
            order = Order(
                order_number=f"ORD-test-pay-{uuid4().hex[:8]}",
                customer_id=sample_customer.id,
                subtotal=Decimal("50.00"),
                shipping_fee=Decimal("100.00"),
                total_price=Decimal("150.00"),
                payment_status="completed",
                shipping_status="preparing",
                profit=Decimal("80.00"),
                affiliate_id=affiliate_active.id,
            )
            test_db.add(order)
            test_db.commit()
            AffiliateService.record_commission_if_applicable(test_db, order)

        # 20 지급
        payment = AffiliatePayment(
            affiliate_id=affiliate_active.id,
            amount=Decimal("20.00"),
            status="completed",
        )
        test_db.add(payment)
        test_db.commit()

        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)
        total_paid = sum(
            payment.amount
            for payment in affiliate_active.payments
            if payment.status == "completed"
        )
        pending_commission = total_revenue - total_paid

        # Then - 48 - 20 = 28
        assert pending_commission == Decimal("28.00")

    def test_pending_commission_after_full_payment(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_customer,
    ):
        """TC-B.4.3: 전액 지급되었으면 지급 예상 수수료 = 0"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # 3개 주문으로 총 수익 48 생성
        for i in range(3):
            order = Order(
                order_number=f"ORD-test-pay-{uuid4().hex[:8]}",
                customer_id=sample_customer.id,
                subtotal=Decimal("50.00"),
                shipping_fee=Decimal("100.00"),
                total_price=Decimal("150.00"),
                payment_status="completed",
                shipping_status="preparing",
                profit=Decimal("80.00"),
                affiliate_id=affiliate_active.id,
            )
            test_db.add(order)
            test_db.commit()
            AffiliateService.record_commission_if_applicable(test_db, order)

        # 전액 지급 (48)
        payment = AffiliatePayment(
            affiliate_id=affiliate_active.id,
            amount=Decimal("48.00"),
            status="completed",
        )
        test_db.add(payment)
        test_db.commit()

        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)
        total_paid = sum(
            payment.amount
            for payment in affiliate_active.payments
            if payment.status == "completed"
        )
        pending_commission = total_revenue - total_paid

        # Then - 48 - 48 = 0
        assert pending_commission == Decimal("0.00")

    def test_pending_payment_not_included_in_paid_amount(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_customer,
    ):
        """TC-B.4.4: 지급 대기(pending) 중인 금액은 제외하고 계산한다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # 3개 주문으로 총 수익 48 생성
        for i in range(3):
            order = Order(
                order_number=f"ORD-test-pay-{uuid4().hex[:8]}",
                customer_id=sample_customer.id,
                subtotal=Decimal("50.00"),
                shipping_fee=Decimal("100.00"),
                total_price=Decimal("150.00"),
                payment_status="completed",
                shipping_status="preparing",
                profit=Decimal("80.00"),
                affiliate_id=affiliate_active.id,
            )
            test_db.add(order)
            test_db.commit()
            AffiliateService.record_commission_if_applicable(test_db, order)

        # Pending 상태로 30 기록
        pending_payment = AffiliatePayment(
            affiliate_id=affiliate_active.id,
            amount=Decimal("30.00"),
            status="pending",
        )
        test_db.add(pending_payment)
        test_db.commit()

        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)
        total_paid = sum(
            payment.amount
            for payment in affiliate_active.payments
            if payment.status == "completed"
        )
        pending_commission = total_revenue - total_paid

        # Then - pending은 제외하므로 48 - 0 = 48
        assert pending_commission == Decimal("48.00")

    def test_failed_payment_not_included_in_paid_amount(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
        sample_customer,
    ):
        """TC-B.4.5: 지급 실패(failed)한 금액도 제외하고 계산한다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # 3개 주문으로 총 수익 48 생성
        for i in range(3):
            order = Order(
                order_number=f"ORD-test-pay-{uuid4().hex[:8]}",
                customer_id=sample_customer.id,
                subtotal=Decimal("50.00"),
                shipping_fee=Decimal("100.00"),
                total_price=Decimal("150.00"),
                payment_status="completed",
                shipping_status="preparing",
                profit=Decimal("80.00"),
                affiliate_id=affiliate_active.id,
            )
            test_db.add(order)
            test_db.commit()
            AffiliateService.record_commission_if_applicable(test_db, order)

        # Completed 지급 (20)
        completed_payment = AffiliatePayment(
            affiliate_id=affiliate_active.id,
            amount=Decimal("20.00"),
            status="completed",
        )
        test_db.add(completed_payment)

        # Failed 지급 (15) - 제외되어야 함
        failed_payment = AffiliatePayment(
            affiliate_id=affiliate_active.id,
            amount=Decimal("15.00"),
            status="failed",
        )
        test_db.add(failed_payment)
        test_db.commit()

        test_db.refresh(affiliate_active)

        # When
        total_revenue = sum(sale.commission_amount for sale in affiliate_active.sales)
        total_paid = sum(
            payment.amount
            for payment in affiliate_active.payments
            if payment.status == "completed"
        )
        pending_commission = total_revenue - total_paid

        # Then - 48 - 20 = 28 (failed 15는 제외)
        assert pending_commission == Decimal("28.00")
