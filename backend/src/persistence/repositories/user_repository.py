"""사용자 저장소 - Data Access Layer"""

from uuid import UUID
from sqlalchemy.orm import Session

from ..models import User as UserORM
from ...workflow.domain.models import User as UserDomain, UserRole


class UserRepository:
    """사용자 저장소 - Domain ↔ ORM 변환"""

    @staticmethod
    def find_user_by_email(db: Session, email: str) -> UserDomain | None:
        """이메일로 사용자 조회"""
        user_orm = db.query(UserORM).filter(UserORM.email == email).first()

        if not user_orm:
            return None

        # ORM → Domain 변환
        return UserRepository._orm_to_domain(user_orm)

    @staticmethod
    def find_user_by_id(db: Session, user_id: UUID) -> UserDomain | None:
        """ID로 사용자 조회"""
        user_orm = db.query(UserORM).filter(UserORM.id == user_id).first()

        if not user_orm:
            return None

        return UserRepository._orm_to_domain(user_orm)

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password_hash: str,
        role: str,
    ) -> UserDomain:
        """사용자 생성"""
        # Domain → ORM 변환
        user_orm = UserORM(
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )

        db.add(user_orm)
        db.commit()
        db.refresh(user_orm)

        # ORM → Domain 변환
        return UserRepository._orm_to_domain(user_orm)

    @staticmethod
    def update_user_password(
        db: Session,
        user_id: UUID,
        password_hash: str,
    ) -> UserDomain | None:
        """비밀번호 업데이트"""
        user_orm = db.query(UserORM).filter(UserORM.id == user_id).first()

        if not user_orm:
            return None

        user_orm.password_hash = password_hash
        db.commit()
        db.refresh(user_orm)

        return UserRepository._orm_to_domain(user_orm)

    @staticmethod
    def _orm_to_domain(user_orm: UserORM) -> UserDomain:
        """ORM 모델 → Domain 모델 변환"""
        return UserDomain(
            id=user_orm.id,
            email=user_orm.email,
            password_hash=user_orm.password_hash,
            role=UserRole(user_orm.role),
            is_active=user_orm.is_active,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
        )
