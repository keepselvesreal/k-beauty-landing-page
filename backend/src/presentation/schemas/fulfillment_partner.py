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


class ShipmentRequest(BaseModel):
    """배송 정보 입력 요청"""
    carrier: str  # 택배사 (LBC, 2GO, Grab Express, Lalamove)
    tracking_number: str  # 운송장 번호

    class Config:
        from_attributes = True


class ShipmentResponse(BaseModel):
    """배송 정보 입력 응답"""
    order_id: UUID
    order_number: str
    status: str  # "shipped"
    carrier: str
    tracking_number: str
    shipped_at: datetime
    email_status: str  # "sent" 또는 "failed"

    class Config:
        from_attributes = True
