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


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str

    class Config:
        example = {
            "current_password": "oldPassword123",
            "new_password": "newPassword456"
        }


class ChangePasswordResponse(BaseModel):
    """비밀번호 변경 응답"""
    message: str

    class Config:
        example = {
            "message": "비밀번호가 성공적으로 변경되었습니다"
        }
