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
# 1. Users (사용자 인증)
# ============================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="fulfillment_partner")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    fulfillment_partner = relationship("FulfillmentPartner", back_populates="user", uselist=False)


# ============================================
# 2. Customers (고객)
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
# 3. Fulfillment Partners (배송담당자)
# ============================================
class FulfillmentPartner(Base):
    __tablename__ = "fulfillment_partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
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
    user = relationship("User", back_populates="fulfillment_partner")
    allocated_inventory = relationship("PartnerAllocatedInventory", back_populates="partner")
    orders = relationship("Order", back_populates="fulfillment_partner")
    shipments = relationship("Shipment", back_populates="partner")


# ============================================
# 4. Products (상품)
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
# 5. Partner Allocated Inventory (배송담당자별 할당 재고)
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
# 6. Orders (주문)
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
    payment_status = Column(String(50), default="pending", nullable=False, index=True)
    paypal_order_id = Column(String(255))
    paypal_capture_id = Column(String(255))
    paypal_fee = Column(Numeric(10, 2))
    profit = Column(Numeric(10, 2), default=80.0)
    paid_at = Column(DateTime)

    # 배송 정보
    shipping_status = Column(String(50), default="preparing", index=True)
    shipped_at = Column(DateTime)

    # 취소 요청
    cancellation_status = Column(String(50), nullable=True)  # null, "cancel_requested", "cancelled"
    cancellation_reason = Column(Text, nullable=True)
    cancellation_requested_at = Column(DateTime, nullable=True)

    # 환불 요청
    refund_status = Column(String(50), nullable=True)  # null, "refund_requested", "refunded"
    refund_reason = Column(Text, nullable=True)
    refund_requested_at = Column(DateTime, nullable=True)

    # 어필리에이트
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey("affiliates.id"), index=True)
    affiliate_commission = Column(Numeric(10, 2))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    customer = relationship("Customer", back_populates="orders")
    fulfillment_partner = relationship("FulfillmentPartner", back_populates="orders")
    affiliate = relationship("Affiliate")
    order_items = relationship("OrderItem", back_populates="order")
    shipment_allocations = relationship("ShipmentAllocation", back_populates="order")
    shipments = relationship("Shipment", back_populates="order")
    email_logs = relationship("EmailLog", back_populates="order")
    affiliate_error_logs = relationship("AffiliateErrorLog", back_populates="order")
    affiliate_sales = relationship("AffiliateSale", back_populates="order")


# ============================================
# 7. Order Items (주문 상품)
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
# 8. Shipment Allocations (배송 할당 기록)
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
# 9. Shipments (배송 기록)
# ============================================
class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("fulfillment_partners.id"), nullable=False)
    carrier = Column(String(100))  # 택배사 (LBC, 2GO, Grab Express, Lalamove)
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
# 10. Email Logs (이메일 발송 로그)
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
# 11. Affiliate Sales (어필리에이트 판매 기록)
# ============================================
class AffiliateSale(Base):
    __tablename__ = "affiliate_sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey("affiliates.id"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    commission_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    affiliate = relationship("Affiliate", back_populates="sales")
    order = relationship("Order", back_populates="affiliate_sales")


# ============================================
# 12. Shipping Rates (지역별 배송료)
# ============================================
class ShippingRate(Base):
    __tablename__ = "shipping_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    region = Column(String(50), unique=True, nullable=False)
    fee = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# 13. Affiliates (어필리에이트)
# ============================================
class Affiliate(Base):
    __tablename__ = "affiliates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    sales = relationship("AffiliateSale", back_populates="affiliate")
    error_logs = relationship("AffiliateErrorLog", back_populates="affiliate")


# ============================================
# 14. Affiliate Error Logs (어필리에이트 오류 기록)
# ============================================
class AffiliateErrorLog(Base):
    __tablename__ = "affiliate_error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey("affiliates.id"), index=True)
    affiliate_code = Column(String(100))
    error_type = Column(String(50), nullable=False)  # "INVALID_CODE" / "INACTIVE_AFFILIATE"
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    order = relationship("Order", back_populates="affiliate_error_logs")
    affiliate = relationship("Affiliate", back_populates="error_logs")


# ============================================
# 15. Settings (시스템 설정)
# ============================================
class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    profit_per_order = Column(Numeric(10, 2), default=80.0)
    affiliate_commission_rate = Column(Numeric(5, 4), default=0.2)
    paypal_fee_rate_avg = Column(Numeric(5, 4))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
