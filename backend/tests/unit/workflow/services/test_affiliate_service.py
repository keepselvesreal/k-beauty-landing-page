"""Affiliate Service 테스트"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.persistence.models import Affiliate, Order, Settings
from src.workflow.services.affiliate_service import AffiliateService


class TestRecordCommissionIfApplicable:
    """Commission 기록"""

    def test_record_commission_success_with_valid_affiliate(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
    ):
        """TC-2.1.1: Affiliate code가 있는 주문의 commission 자동 기록"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        # Order에 affiliate_id 설정
        order_with_customer.affiliate_id = affiliate_active.id
        order_with_customer.status = "paid"
        test_db.add(order_with_customer)
        test_db.commit()

        # Settings 생성
        settings = Settings(
            profit_per_order=Decimal("80.00"),
            affiliate_commission_rate=Decimal("0.2"),
        )
        test_db.add(settings)
        test_db.commit()

        # When
        AffiliateService.record_commission_if_applicable(test_db, order_with_customer)

        # Then
        # affiliate_sales 확인
        assert order_with_customer.affiliate_sales
        affiliate_sale = order_with_customer.affiliate_sales[0]
        assert affiliate_sale.affiliate_id == affiliate_active.id
        assert affiliate_sale.commission_amount == Decimal("16.00")

    def test_no_commission_without_affiliate(
        self,
        test_db: Session,
        order_with_customer: Order,
    ):
        """TC-2.1.2: Affiliate code 없는 경우 commission 미기록"""
        # Given
        order_with_customer.affiliate_id = None
        order_with_customer.status = "paid"
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
