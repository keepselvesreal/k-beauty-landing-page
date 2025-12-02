"""인증 관련 Pydantic 스키마 - HTTP DTO"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str
    role: str = "fulfillment-partner"  # 기본값: fulfillment-partner


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
