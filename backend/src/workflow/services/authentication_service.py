"""인증 서비스 - Business Logic Layer"""

import hashlib
from sqlalchemy.orm import Session

from ..domain.models import User as UserDomain, UserRole
from ...persistence.repositories.user_repository import UserRepository
from ...utils.exceptions import AuthenticationError


class AuthenticationService:
    """인증 서비스 - 비즈니스 규칙만 실행"""

    @staticmethod
    def hash_password(password: str) -> str:
        """비즈니스 규칙: 비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """비즈니스 규칙: 비밀번호 검증"""
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    @staticmethod
    def authenticate_user_by_email(
        db: Session,
        email: str,
        password: str,
    ) -> UserDomain:
        """비즈니스 규칙: 이메일과 비밀번호로 사용자 인증"""

        # Repository를 통해 Domain 모델 조회
        user = UserRepository.find_user_by_email(db, email)

        if not user:
            raise AuthenticationError(
                code="USER_NOT_FOUND",
                message="등록되지 않은 이메일입니다.",
            )

        if not user.is_active:
            raise AuthenticationError(
                code="USER_INACTIVE",
                message="비활성화된 계정입니다.",
            )

        if not AuthenticationService.verify_password(password, user.password_hash):
            raise AuthenticationError(
                code="INVALID_PASSWORD",
                message="비밀번호가 일치하지 않습니다.",
            )

        return user  # Domain 모델 반환
