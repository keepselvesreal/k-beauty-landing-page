"""Unit 테스트용 공통 fixture"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.persistence.models import (
    Product,
    FulfillmentPartner,
)


@pytest.fixture
def sample_product(test_db: Session):
    """테스트용 상품 (기본: 가격 50.00)"""
    product = Product(
        name="Test Product",
        description="Test product for unit tests",
        price=Decimal("50.00"),
        sku="TEST-UNIT-001",
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


@pytest.fixture
def sample_partner(test_db: Session):
    """테스트용 배송담당자 (기본: 활성화, last_allocated_at 없음)"""
    partner = FulfillmentPartner(
        name="Test Partner",
        email="test.partner@example.com",
        phone="09123456789",
        address="Test Address",
        region="NCR",
        is_active=True,
    )
    test_db.add(partner)
    test_db.commit()
    test_db.refresh(partner)
    return partner


@pytest.fixture
def partner_with_allocation_history(test_db: Session):
    """할당 이력이 있는 배송담당자 (3일 전 할당)"""
    partner = FulfillmentPartner(
        name="Partner with History",
        email="history.partner@example.com",
        phone="09123456790",
        address="Test Address",
        region="NCR",
        is_active=True,
        last_allocated_at=datetime.utcnow() - timedelta(days=3),
    )
    test_db.add(partner)
    test_db.commit()
    test_db.refresh(partner)
    return partner


@pytest.fixture
def inactive_partner(test_db: Session):
    """비활성 배송담당자"""
    partner = FulfillmentPartner(
        name="Inactive Partner",
        email="inactive.partner@example.com",
        phone="09123456791",
        address="Test Address",
        region="NCR",
        is_active=False,
    )
    test_db.add(partner)
    test_db.commit()
    test_db.refresh(partner)
    return partner
