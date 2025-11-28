"""Integration 테스트용 fixture 및 테스트 데이터"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from src.persistence.models import (
    Customer,
    Product,
    FulfillmentPartner,
    PartnerAllocatedInventory,
    ShippingRate,
)


@pytest.fixture
def sample_customer(test_db: Session):
    """샘플 고객"""
    customer = Customer(
        email="test.customer@example.com",
        name="테스트 고객",
        phone="09123456789",
        address="Manila, Philippines",
        region="NCR",
    )
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    return customer


@pytest.fixture
def sample_product(test_db: Session):
    """샘플 상품"""
    product = Product(
        name="K-Beauty Secret Essence",
        description="Premium Korean beauty essence with 10 natural ingredients",
        price=Decimal("50.00"),
        sku="KBSE-001",
        image_url="https://example.com/kbse-001.jpg",
        is_active=True,
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product


@pytest.fixture
def sample_fulfillment_partner(test_db: Session):
    """샘플 배송담당자"""
    partner = FulfillmentPartner(
        name="Manila Express Partner",
        email="partner1@example.com",
        phone="09123456789",
        address="Manila Warehouse",
        region="NCR",
        is_active=True,
    )
    test_db.add(partner)
    test_db.commit()
    test_db.refresh(partner)
    return partner


@pytest.fixture
def sample_inventory(test_db: Session, sample_fulfillment_partner, sample_product):
    """샘플 배송담당자 재고"""
    inventory = PartnerAllocatedInventory(
        partner_id=sample_fulfillment_partner.id,
        product_id=sample_product.id,
        allocated_quantity=100,
        remaining_quantity=100,
        stock_version=0,
    )
    test_db.add(inventory)
    test_db.commit()
    test_db.refresh(inventory)
    return inventory


@pytest.fixture
def sample_shipping_rates(test_db: Session):
    """샘플 배송료"""
    rates = [
        ShippingRate(region="NCR", fee=Decimal("100.00")),
        ShippingRate(region="Luzon", fee=Decimal("120.00")),
        ShippingRate(region="Visayas", fee=Decimal("140.00")),
        ShippingRate(region="Mindanao", fee=Decimal("160.00")),
    ]
    test_db.add_all(rates)
    test_db.commit()
    for rate in rates:
        test_db.refresh(rate)
    return rates


@pytest.fixture
def complete_test_data(test_db: Session, sample_customer, sample_product,
                       sample_fulfillment_partner, sample_inventory, sample_shipping_rates):
    """완전한 테스트 데이터 (customer, product, partner, inventory, shipping rates)"""
    return {
        "customer": sample_customer,
        "product": sample_product,
        "partner": sample_fulfillment_partner,
        "inventory": sample_inventory,
        "shipping_rates": sample_shipping_rates,
        "db": test_db,
    }
