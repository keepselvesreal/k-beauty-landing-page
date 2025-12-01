"""Unit 테스트용 공통 fixture"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.persistence.models import (
    Product,
    FulfillmentPartner,
    Affiliate,
    Customer,
    Order,
    ShippingRate,
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


# ============================================
# Affiliate 관련 픽스처
# ============================================
@pytest.fixture
def affiliate_active(test_db: Session):
    """활성화된 Affiliate"""
    affiliate = Affiliate(
        code="aff-active-1234",
        name="Active Affiliate Partner",
        email="active@affiliate.example.com",
        is_active=True,
    )
    test_db.add(affiliate)
    test_db.commit()
    test_db.refresh(affiliate)
    return affiliate


@pytest.fixture
def affiliate_inactive(test_db: Session):
    """비활성화된 Affiliate"""
    affiliate = Affiliate(
        code="aff-inactive-5678",
        name="Inactive Affiliate Partner",
        email="inactive@affiliate.example.com",
        is_active=False,
    )
    test_db.add(affiliate)
    test_db.commit()
    test_db.refresh(affiliate)
    return affiliate


# ============================================
# Order 관련 픽스처
# ============================================
@pytest.fixture
def sample_customer(test_db: Session):
    """기본 고객"""
    customer = Customer(
        email="customer@example.com",
        name="Kim Taesoo",
        phone="+63-901-234-5678",
        address="123 Main St, Manila, NCR, Philippines",
        region="NCR",
    )
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    return customer


@pytest.fixture
def shipping_rate_ncr(test_db: Session):
    """NCR 지역 배송료"""
    rate = ShippingRate(
        region="NCR",
        fee=Decimal("100.00"),
    )
    test_db.add(rate)
    test_db.commit()
    test_db.refresh(rate)
    return rate


@pytest.fixture
def order_with_customer(test_db: Session, sample_customer: Customer, sample_product: Product, shipping_rate_ncr: ShippingRate):
    """고객 정보가 있는 주문"""
    order = Order(
        order_number="ORD-test-001",
        customer_id=sample_customer.id,
        subtotal=Decimal("50.00"),
        shipping_fee=Decimal("100.00"),
        total_price=Decimal("150.00"),
        payment_status="pending",
        profit=Decimal("80.00"),
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)
    return order
