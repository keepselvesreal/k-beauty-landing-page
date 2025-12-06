"""관리자 서비스 - Business Logic Layer"""

from sqlalchemy.orm import Session
from uuid import uuid4

from ..domain.models import User as UserDomain, UserRole
from ...persistence.repositories.user_repository import UserRepository
from ...persistence.models import FulfillmentPartner
from ...infrastructure.exceptions import AuthenticationError


class AdminService:
    """관리자 서비스 - 사용자 관리"""

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        role: str,
    ) -> UserDomain:
        """사용자 생성 (User + FulfillmentPartner)"""
        from .authentication_service import AuthenticationService

        # 1. 이메일 중복 확인
        existing_user = UserRepository.find_user_by_email(db, email)
        if existing_user:
            raise AuthenticationError(
                code="EMAIL_ALREADY_EXISTS",
                message="이미 등록된 이메일입니다.",
            )

        # 2. 역할 유효성 검증 (fulfillment_partner, influencer, admin 허용)
        valid_roles = ["fulfillment_partner", "influencer", "admin"]
        if role not in valid_roles:
            raise AuthenticationError(
                code="INVALID_ROLE",
                message=f"유효하지 않은 역할입니다. ({', '.join(valid_roles)})",
            )

        # 3. 비밀번호 해싱
        password_hash = AuthenticationService.hash_password(password)

        # 4. 사용자 생성
        user = UserRepository.create_user(
            db,
            email=email,
            password_hash=password_hash,
            role=role,
        )

        # 5. 배송담당자인 경우 FulfillmentPartner도 생성
        if role == "fulfillment_partner":
            # 이메일에서 이름 추출 (예: taesu@naver.com → taesu)
            name = email.split("@")[0]

            fulfillment_partner = FulfillmentPartner(
                id=uuid4(),
                user_id=user.id,
                name=name,
                email=email,
                phone=None,
                address=None,
                region=None,
                is_active=True,
            )
            db.add(fulfillment_partner)
            db.commit()
            db.refresh(fulfillment_partner)

        return user
