"""상품 관련 Pydantic 스키마"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductResponse(BaseModel):
    """상품 응답 스키마"""
    id: UUID
    name: str
    description: str
    price: Decimal
    sku: str
    image_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
