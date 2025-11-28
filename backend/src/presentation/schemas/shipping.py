"""배송료 관련 Pydantic 스키마"""

from decimal import Decimal
from pydantic import BaseModel


class ShippingRateResponse(BaseModel):
    """배송료 응답 스키마"""
    region: str
    fee: Decimal

    class Config:
        from_attributes = True


class ShippingRateUpdate(BaseModel):
    """배송료 업데이트 스키마"""
    fee: float
