"""Affiliate Repository 테스트"""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.persistence.models import Affiliate, AffiliateErrorLog, AffiliateSale, Order
from src.persistence.repositories.affiliate_repository import AffiliateRepository


class TestGetAffiliateByCode:
    """Affiliate 코드로 조회"""

    def test_get_affiliate_by_code_success(self, test_db: Session, affiliate_active: Affiliate):
        """TC-3.1.1: Affiliate 코드로 조회 - 존재하는 경우"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        # When
        result = AffiliateRepository.get_affiliate_by_code(test_db, affiliate_active.code)

        # Then
        assert result is not None
        assert result.code == affiliate_active.code
        assert result.is_active is True

    def test_get_affiliate_by_code_not_found(self, test_db: Session):
        """TC-3.1.2: Affiliate 코드로 조회 - 존재하지 않는 경우"""
        # Given
        invalid_code = "aff-invalid-9999"

        # When
        result = AffiliateRepository.get_affiliate_by_code(test_db, invalid_code)

        # Then
        assert result is None


class TestCreateAffiliateErrorLog:
    """Affiliate Error Log 생성"""

    def test_create_affiliate_error_log_invalid_code(
        self, test_db: Session, order_with_customer: Order
    ):
        """TC-3.1.3: Affiliate Error Log 생성 - 유효하지 않은 코드"""
        # Given
        test_db.add(order_with_customer)
        test_db.commit()

        # When
        error_log = AffiliateRepository.create_affiliate_error_log(
            test_db,
            order_id=order_with_customer.id,
            affiliate_code="aff-invalid-9999",
            error_type="INVALID_CODE",
            error_message="Affiliate code not found",
        )

        # Then
        assert error_log is not None
        assert error_log.order_id == order_with_customer.id
        assert error_log.affiliate_code == "aff-invalid-9999"
        assert error_log.error_type == "INVALID_CODE"
        assert error_log.error_message == "Affiliate code not found"

    def test_create_affiliate_error_log_inactive_affiliate(
        self, test_db: Session, order_with_customer: Order, affiliate_inactive: Affiliate
    ):
        """TC-3.1.4: Affiliate Error Log 생성 - 비활성화된 Affiliate"""
        # Given
        test_db.add(order_with_customer)
        test_db.add(affiliate_inactive)
        test_db.commit()

        # When
        error_log = AffiliateRepository.create_affiliate_error_log(
            test_db,
            order_id=order_with_customer.id,
            affiliate_code=affiliate_inactive.code,
            error_type="INACTIVE_AFFILIATE",
            error_message="Affiliate is inactive",
        )

        # Then
        assert error_log is not None
        assert error_log.error_type == "INACTIVE_AFFILIATE"
        assert error_log.affiliate_code == affiliate_inactive.code


class TestCreateAffiliateSale:
    """Affiliate Sale 생성"""

    def test_create_affiliate_sale_success(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
        order_with_customer: Order,
    ):
        """TC-3.1.5: Affiliate Sale 생성"""
        # Given
        test_db.add(affiliate_active)
        test_db.add(order_with_customer)
        test_db.commit()

        commission_amount = Decimal("16.00")

        # When
        affiliate_sale = AffiliateRepository.create_affiliate_sale(
            test_db,
            affiliate_id=affiliate_active.id,
            order_id=order_with_customer.id,
            commission_amount=commission_amount,
        )

        # Then
        assert affiliate_sale is not None
        assert affiliate_sale.affiliate_id == affiliate_active.id
        assert affiliate_sale.order_id == order_with_customer.id
        assert affiliate_sale.commission_amount == commission_amount
