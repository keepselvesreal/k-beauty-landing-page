"""문의(Inquiry) 관련 Pydantic 스키마"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InquiryRequest(BaseModel):
    """문의 요청"""
    inquiry_type: str = Field(..., description="문의 타입: influencer, fulfillment_partner, customer")
    message: str = Field(..., description="문의 내용")
    reply_to_email: Optional[str] = Field(None, description="회신받을 이메일 (선택사항)")

    class Config:
        from_attributes = True


class InquiryResponse(BaseModel):
    """문의 응답"""
    status: str  # "sent" 또는 "failed"
    message: str
    inquiry_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class InquiryDetailResponse(BaseModel):
    """문의 상세 조회 응답"""
    id: UUID
    inquiry_type: str
    sender_id: Optional[UUID]
    reply_to_email: str
    message: str
    status: str  # "unread", "read"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InquiryListResponse(BaseModel):
    """문의 목록 조회 응답"""
    total: int
    page: int
    page_size: int
    inquiries: list[InquiryDetailResponse]

    class Config:
        from_attributes = True


class InquiryStatusUpdateRequest(BaseModel):
    """문의 상태 변경 요청"""
    status: str = Field(..., description="변경할 상태: unread, read")

    class Config:
        from_attributes = True
