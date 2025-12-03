"""관리자 관련 Pydantic 스키마 - HTTP DTO"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============================================
# 사용자 생성
# ============================================
class CreateUserRequest(BaseModel):
    """사용자 생성 요청"""
    email: EmailStr
    password: str
    role: str  # "fulfillment_partner" 또는 "influencer"


class CreateUserResponse(BaseModel):
    """사용자 생성 응답"""
    user_id: str
    email: str
    role: str


# ============================================
# 재고 관리
# ============================================
class InventoryItem(BaseModel):
    """재고 목록 항목"""
    inventory_id: UUID
    partner_id: UUID
    partner_name: str
    product_id: UUID
    product_name: str
    current_quantity: int
    allocated_quantity: int
    last_adjusted_at: datetime


class InventoryListResponse(BaseModel):
    """재고 목록 응답"""
    inventories: list[InventoryItem]
    total_count: int


class AdjustInventoryRequest(BaseModel):
    """재고 조정 요청"""
    new_quantity: int = Field(..., ge=0, description="새로운 수량 (0 이상)")
    reason: str | None = Field(None, description="조정 사유 (선택적)")


class AdjustInventoryResponse(BaseModel):
    """재고 조정 응답"""
    inventory_id: UUID
    old_quantity: int
    new_quantity: int
    log_id: UUID
    updated_at: datetime


class InventoryAdjustmentHistoryItem(BaseModel):
    """재고 조정 이력 항목"""
    log_id: UUID
    old_quantity: int
    new_quantity: int
    reason: str | None
    adjusted_at: datetime


class InventoryHistoryResponse(BaseModel):
    """재고 조정 이력 응답"""
    inventory_id: UUID
    partner_name: str
    product_name: str
    history: list[InventoryAdjustmentHistoryItem]


# ============================================
# 배송 관리
# ============================================
class ShipmentItem(BaseModel):
    """배송 목록 항목"""
    shipment_id: UUID
    order_id: UUID
    order_number: str
    customer_name: str
    customer_address: str
    total_price: float
    status: str
    carrier: str | None
    tracking_number: str | None
    partner_name: str
    shipped_at: datetime | None
    delivered_at: datetime | None


class ShipmentListResponse(BaseModel):
    """배송 목록 응답"""
    shipments: list[ShipmentItem]
    total_count: int


class CompleteShipmentResponse(BaseModel):
    """배송 완료 응답"""
    success: bool
    shipment_id: UUID
    order_id: UUID
    order_number: str
    status: str
    delivered_at: datetime
