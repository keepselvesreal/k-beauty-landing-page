"""SQLAlchemy ORM 모델"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.persistence.database import Base


# ============================================
# 1. Customers (고객)
# ============================================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    region = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    orders = relationship("Order", back_populates="customer")


# ============================================
# 2. Fulfillment Partners (배송담당자)
# ============================================
class FulfillmentPartner(Base):
    __tablename__ = "fulfillment_partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    phone = Column(String(20))
    address = Column(Text)
    region = Column(String(50))
    is_active = Column(Boolean, default=True, index=True)
    last_allocated_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    allocated_inventory = relationship("PartnerAllocatedInventory", back_populates="partner")
    orders = relationship("Order", back_populates="fulfillment_partner")
    shipments = relationship("Shipment", back_populates="partner")


# ============================================
# 3. Products (상품)
# ============================================
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    sku = Column(String(100), unique=True)
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    allocated_inventory = relationship("PartnerAllocatedInventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


# ============================================
# 4. Partner Allocated Inventory (배송담당자별 할당 재고)
# ============================================
class PartnerAllocatedInventory(Base):
    __tablename__ = "partner_allocated_inventory"
    __table_args__ = (UniqueConstraint("partner_id", "product_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("fulfillment_partners.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    allocated_quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False, index=True)
    stock_version = Column(Integer, default=0)
    allocated_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    partner = relationship("FulfillmentPartner", back_populates="allocated_inventory")
    product = relationship("Product", back_populates="allocated_inventory")


# ============================================
# 5. Orders (주문)
# ============================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    fulfillment_partner_id = Column(UUID(as_uuid=True), ForeignKey("fulfillment_partners.id"), index=True)

    # 가격 정보
    subtotal = Column(Numeric(10, 2), nullable=False)
    shipping_fee = Column(Numeric(10, 2), default=0)
    total_price = Column(Numeric(10, 2), nullable=False)

    # 결제 정보
    status = Column(String(50), default="pending", nullable=False, index=True)
    paypal_order_id = Column(String(255))
    paypal_capture_id = Column(String(255))
    paypal_fee = Column(Numeric(10, 2))
    profit = Column(Numeric(10, 2), default=80.0)
    paid_at = Column(DateTime)

    # 배송 정보
    shipping_status = Column(String(50), default="pending", index=True)
    shipped_at = Column(DateTime)

    # 어필리에이트
    affiliate_code = Column(String(100))
    affiliate_commission = Column(Numeric(10, 2))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    customer = relationship("Customer", back_populates="orders")
    fulfillment_partner = relationship("FulfillmentPartner", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    shipment_allocations = relationship("ShipmentAllocation", back_populates="order")
    shipments = relationship("Shipment", back_populates="order")
    email_logs = relationship("EmailLog", back_populates="order")
    affiliate_sales = relationship("AffiliateSale", back_populates="order")


# ============================================
# 6. Order Items (주문 상품)
# ============================================
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    shipment_allocations = relationship("ShipmentAllocation", back_populates="order_item")


# ============================================
# 7. Shipment Allocations (배송 할당 기록)
# ============================================
class ShipmentAllocation(Base):
    __tablename__ = "shipment_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id"), nullable=False)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("fulfillment_partners.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    allocated_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    order = relationship("Order", back_populates="shipment_allocations")
    order_item = relationship("OrderItem", back_populates="shipment_allocations")
    partner = relationship("FulfillmentPartner")


# ============================================
# 8. Shipments (배송 기록)
# ============================================
class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("fulfillment_partners.id"), nullable=False)
    tracking_number = Column(String(255))
    status = Column(String(50), default="preparing", index=True)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    order = relationship("Order", back_populates="shipments")
    partner = relationship("FulfillmentPartner", back_populates="shipments")


# ============================================
# 9. Email Logs (이메일 발송 로그)
# ============================================
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    recipient_email = Column(String(255))
    email_type = Column(String(100))
    status = Column(String(50), index=True)
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    order = relationship("Order", back_populates="email_logs")


# ============================================
# 10. Affiliate Sales (어필리에이트 판매 기록)
# ============================================
class AffiliateSale(Base):
    __tablename__ = "affiliate_sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    affiliate_code = Column(String(100), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    commission_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    order = relationship("Order", back_populates="affiliate_sales")


# ============================================
# 11. Shipping Rates (지역별 배송료)
# ============================================
class ShippingRate(Base):
    __tablename__ = "shipping_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    region = Column(String(50), unique=True, nullable=False)
    fee = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# 12. Settings (시스템 설정)
# ============================================
class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    profit_per_order = Column(Numeric(10, 2), default=80.0)
    paypal_fee_rate_avg = Column(Numeric(5, 4))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
