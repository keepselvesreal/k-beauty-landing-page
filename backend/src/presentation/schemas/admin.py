"""관리자 관련 Pydantic 스키마 - HTTP DTO"""

from pydantic import BaseModel, EmailStr


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
