"""도메인 엔티티 - 순수 비즈니스 모델"""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from datetime import datetime


class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"
    FULFILLMENT_PARTNER = "fulfillment_partner"
    INFLUENCER = "influencer"


@dataclass
class User:
    """사용자 - 순수 비즈니스 모델"""
    id: UUID
    email: str
    password_hash: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class FulfillmentPartner:
    """배송담당자 - 순수 비즈니스 모델"""
    id: UUID
    user_id: UUID
    name: str
    email: str
    phone: str | None
    address: str | None
    region: str | None
    is_active: bool
    last_allocated_at: datetime | None
    created_at: datetime
    updated_at: datetime
