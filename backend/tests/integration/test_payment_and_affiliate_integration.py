"""결제 완료 후 어필리에이트 Commission 기록 통합테스트"""

from decimal import Decimal
from unittest.mock import patch, Mock

import pytest

from src.workflow.services.affiliate_service import AffiliateService
from src.workflow.services.order_service import OrderService
from src.persistence.models import Affiliate


class TestPaymentAndAffiliateIntegration:
    """결제 완료 후 어필리에이트 Commission 기록 통합테스트"""

    def test_commission_recorded_after_payment_with_valid_affiliate(
        self, client, complete_test_data
    ):
        """TC-2.1.1 Integration: 결제 완료 후 valid affiliate commission 자동 기록"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: Affiliate code를 지정해서 Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=2,
            region="NCR",
        )
        order = order_result["order"]

        # Step 2: Affiliate 검증 및 ID 설정
        affiliate_id = AffiliateService.validate_and_record_affiliate_on_order_creation(
            db,
            order,
            data["affiliate"].code,
        )
        order.affiliate_id = affiliate_id
        db.commit()

        # ===== WHEN (실행 동작) =====
        # Step 3: 결제 초기화
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-AFFILIATE-TEST-001"
            mock_payment.state = "created"
            mock_payment.links = [
                {'rel': 'approval_url', 'href': 'https://www.sandbox.paypal.com/checkoutnow?token=AFF'},
            ]
            mock_payment_class.return_value = mock_payment

            payment_result = OrderService.initiate_payment(db, order.id)

        # Step 4: 결제 완료 상태로 변경
        order.status = "paid"
        db.commit()

        # Step 5: Commission 기록 (핵심 동작)
        AffiliateService.record_commission_if_applicable(db, order)

        # ===== THEN (예상 결과) =====
        assert len(order.affiliate_sales) > 0
        affiliate_sale = order.affiliate_sales[0]
        assert affiliate_sale.affiliate_id == data["affiliate"].id
        assert affiliate_sale.commission_amount == Decimal("16.00")  # 80 * 0.2

    def test_no_commission_without_affiliate(self, client, complete_test_data):
        """TC-2.1.2 Integration: Affiliate code 없는 경우 commission 미기록"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: Order 생성 (affiliate 없음)
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=1,
            region="NCR",
        )
        order = order_result["order"]

        # ===== WHEN (실행 동작) =====
        # Step 2: 결제 완료 상태로 변경
        order.status = "paid"
        db.commit()

        # Step 3: Commission 기록 시도 (핵심 동작)
        AffiliateService.record_commission_if_applicable(db, order)

        # ===== THEN (예상 결과) =====
        assert len(order.affiliate_sales) == 0

    def test_error_log_created_for_invalid_affiliate_code(
        self, client, complete_test_data
    ):
        """TC-2.1.4 Integration: 존재하지 않는 affiliate code → 오류 기록"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=1,
            region="NCR",
        )
        order = order_result["order"]

        # ===== WHEN (실행 동작) =====
        # Step 2: 유효하지 않은 Affiliate code 검증 (핵심 동작)
        result = AffiliateService.validate_and_record_affiliate_on_order_creation(
            db,
            order,
            "aff-invalid-9999",
        )

        # ===== THEN (예상 결과) =====
        assert result is None
        assert len(order.affiliate_error_logs) == 1
        error_log = order.affiliate_error_logs[0]
        assert error_log.error_type == "INVALID_CODE"
        assert error_log.affiliate_code == "aff-invalid-9999"

    def test_error_log_created_for_inactive_affiliate(
        self, client, complete_test_data
    ):
        """TC-2.1.5 Integration: 비활성화된 affiliate → 오류 기록"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: 비활성화된 Affiliate 생성
        inactive_affiliate = Affiliate(
            code="aff-inactive-integration",
            name="Inactive Affiliate",
            email="inactive@example.com",
            is_active=False,
        )
        db.add(inactive_affiliate)
        db.commit()

        # Step 2: Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=1,
            region="NCR",
        )
        order = order_result["order"]

        # ===== WHEN (실행 동작) =====
        # Step 3: 비활성화된 Affiliate code 검증 (핵심 동작)
        result = AffiliateService.validate_and_record_affiliate_on_order_creation(
            db,
            order,
            inactive_affiliate.code,
        )

        # ===== THEN (예상 결과) =====
        assert result is None
        assert len(order.affiliate_error_logs) == 1
        error_log = order.affiliate_error_logs[0]
        assert error_log.error_type == "INACTIVE_AFFILIATE"
        assert error_log.affiliate_code == inactive_affiliate.code

    def test_commission_calculation_accuracy_in_integration(
        self, client, complete_test_data
    ):
        """TC-2.1.3 Integration: Commission 금액 정확성 검증"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=5,  # 5 * 50 = 250
            region="Luzon",  # shipping 120
        )
        order = order_result["order"]

        # Step 2: Affiliate 설정
        affiliate_id = AffiliateService.validate_and_record_affiliate_on_order_creation(
            db,
            order,
            data["affiliate"].code,
        )
        order.affiliate_id = affiliate_id
        db.commit()

        # ===== WHEN (실행 동작) =====
        # Step 3: 결제 완료
        order.status = "paid"
        db.commit()

        # Step 4: Commission 기록 (핵심 동작)
        AffiliateService.record_commission_if_applicable(db, order)

        # ===== THEN (예상 결과) =====
        assert len(order.affiliate_sales) == 1
        affiliate_sale = order.affiliate_sales[0]
        # profit = 80.00, commission_rate = 0.2
        # commission = 80.00 * 0.2 = 16.00
        assert affiliate_sale.commission_amount == Decimal("16.00")
