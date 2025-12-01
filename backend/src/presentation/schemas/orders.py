"""주문 관련 Pydantic 스키마"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    """주문 상품 생성 스키마"""
    product_id: UUID
    quantity: int


class OrderCreate(BaseModel):
    """주문 생성 스키마"""
    customer_id: UUID
    product_id: UUID
    quantity: int
    region: str  # 배송료 계산용


class OrderItemResponse(BaseModel):
    """주문 상품 응답 스키마"""
    id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """주문 응답 스키마"""
    id: UUID
    order_number: str
    customer_id: UUID
    subtotal: Decimal
    shipping_fee: Decimal
    total_price: Decimal
    payment_status: str  # pending, paid, payment_failed, cancelled
    shipping_status: str  # preparing, shipped, delivered
    paypal_order_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
