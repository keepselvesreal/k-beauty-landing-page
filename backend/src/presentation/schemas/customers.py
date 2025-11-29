"""고객 관련 Pydantic 스키마"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    """고객 생성 스키마"""
    email: EmailStr
    name: str
    phone: str
    address: str
    region: Optional[str] = None


class CustomerResponse(BaseModel):
    """고객 응답 스키마"""
    id: UUID
    email: str
    name: str
    phone: str
    address: str
    region: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
