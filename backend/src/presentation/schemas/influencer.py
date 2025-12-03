"""인플루언서 관련 Pydantic 스키마"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class InfluencerDashboardResponse(BaseModel):
    """인플루언서 대시보드 응답"""
    affiliate_code: str
    affiliate_url: str  # 추적 URL (예: https://example.com?aff=AFFILIATE_CODE)
    total_clicks: int
    total_sales: int  # 판매 건수
    cumulative_revenue: Decimal  # 누적 수익
    pending_commission: Decimal  # 지급 예상 수수료
    next_payment_date: Optional[datetime]  # 지급 예정 날짜

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AffiliateClickRequest(BaseModel):
    """어필리에이트 클릭 요청"""
    code: str  # 어필리에이트 코드

    class Config:
        from_attributes = True


class AffiliateClickResponse(BaseModel):
    """어필리에이트 클릭 응답"""
    status: str  # "success" 또는 "error"
    message: str

    class Config:
        from_attributes = True
