"""배송담당자 관련 Pydantic 스키마"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProductInOrder(BaseModel):
    """주문 내 상품 정보"""
    name: str
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class FulfillmentPartnerOrderResponse(BaseModel):
    """배송담당자가 조회하는 주문 정보"""
    order_id: UUID
    order_number: str
    customer_email: str
    products: list[ProductInOrder]
    shipping_address: str
    total_price: Decimal
    status: str  # "preparing"
    created_at: datetime

    class Config:
        from_attributes = True


class FulfillmentPartnerOrdersListResponse(BaseModel):
    """배송담당자 주문 목록 응답"""
    partner_id: UUID
    partner_name: str
    orders: list[FulfillmentPartnerOrderResponse]

    class Config:
        from_attributes = True
