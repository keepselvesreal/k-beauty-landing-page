"""인증 라우터 - Presentation Layer (통합 버전)"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ....persistence.database import get_db
from ....persistence.models import User, FulfillmentPartner, Affiliate
from ....workflow.services.authentication_service import AuthenticationService
from ....infrastructure.auth import JWTTokenManager
from ....infrastructure.exceptions import AuthenticationError
from ...schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest, ChangePasswordResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class CurrentUserResponse(BaseModel):
    """현재 사용자 정보 응답"""
    user_id: str
    email: str
    role: str


class TestAccountResponse(BaseModel):
    """테스트 계정 정보 응답"""
    email: str
    password: str
    role: str
    name: str


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """현재 사용자 정보 추출 (의존성) - 모든 역할 지원"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Authorization 헤더가 필요합니다.",
            },
        )

    # Bearer 토큰 추출
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_FORMAT",
                "message": "유효하지 않은 토큰 형식입니다.",
            },
        )

    token = parts[1]

    # JWT 토큰 검증
    try:
        payload = JWTTokenManager.verify_access_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )

    # 사용자 조회
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "사용자를 찾을 수 없습니다.",
            },
        )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    통합 로그인 (모든 역할 지원)

    Request:
    {
        "email": "user@example.com",
        "password": "password123",
        "role": "fulfillment-partner" or "influencer" or "admin"
    }
    """
    try:
        # Service 계층에서 인증 처리
        user = AuthenticationService.authenticate_user_by_email(
            db,
            email=credentials.email,
            password=credentials.password,
        )

        # 요청된 역할과 실제 역할이 일치하는지 검증
        user_actual_role = user.role.value if hasattr(user.role, 'value') else user.role
        requested_role = credentials.role.replace('-', '_')

        if user_actual_role != requested_role:
            raise AuthenticationError(
                code="ROLE_MISMATCH",
                message=f"사용자의 역할은 {user_actual_role}입니다. {credentials.role}로 로그인할 수 없습니다.",
            )

        # 토큰 생성
        token_payload = {
            "user_id": str(user.id),
            "role": user_actual_role,
            "email": user.email,
        }
        access_token = JWTTokenManager.create_access_token(token_payload)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    authorization: str = Header(None),
):
    """
    통합 사용자 정보 조회 (모든 역할 지원)

    Returns:
    {
        "user_id": "uuid",
        "email": "user@example.com",
        "role": "fulfillment-partner" or "influencer" or "admin"
    }
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Authorization 헤더가 필요합니다.",
            },
        )

    # Bearer 토큰 추출
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_FORMAT",
                "message": "유효하지 않은 토큰 형식입니다.",
            },
        )

    token = parts[1]

    # JWT 토큰 검증
    try:
        payload = JWTTokenManager.verify_access_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )

    # 토큰의 정보 반환 (역할을 kebab-case로 변환)
    role = payload.get("role", "").replace("_", "-")
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": role,
    }


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    비밀번호 변경 (통합, 모든 역할 지원)

    Request:
    {
        "current_password": "oldPassword123",
        "new_password": "newPassword456"
    }

    Response:
    {
        "message": "비밀번호가 성공적으로 변경되었습니다"
    }
    """
    try:
        # 현재 비밀번호 검증
        is_valid = AuthenticationService.verify_password(
            request.current_password,
            current_user.password_hash,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_PASSWORD",
                    "message": "현재 비밀번호가 올바르지 않습니다.",
                },
            )

        # 새 비밀번호로 업데이트
        current_user.password_hash = AuthenticationService.hash_password(
            request.new_password
        )
        db.commit()

        return {
            "message": "비밀번호가 성공적으로 변경되었습니다"
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}",
            },
        )


@router.get("/test-accounts", response_model=List[TestAccountResponse])
async def get_test_accounts(db: Session = Depends(get_db)):
    """
    현재 등록된 테스트 계정 조회 (배송담당자, 인플루언서)

    더미 데이터가 생성되거나 변경되면 항상 최신 정보를 반환합니다.
    password는 seeders.py의 규칙에 따라 생성됩니다:
    - 배송담당자: Partner@{region}123
    - 인플루언서: test123456

    Returns:
    [
        {
            "email": "ncr.partner@example.com",
            "password": "Partner@NCR123",
            "role": "fulfillment-partner",
            "name": "조선미녀 필리핀 배송담당자"
        },
        {
            "email": "influencer@example.com",
            "password": "test123456",
            "role": "influencer",
            "name": "Kim Taesoo (인플루언서)"
        }
    ]
    """
    try:
        test_accounts = []

        # 배송담당자 계정 조회
        fulfillment_partners = (
            db.query(User, FulfillmentPartner)
            .join(FulfillmentPartner, User.id == FulfillmentPartner.user_id)
            .filter(User.role == "fulfillment_partner")
            .all()
        )

        for user, partner in fulfillment_partners:
            # seeders.py 규칙: password = f"Partner@{partner_data['region']}123"
            password = f"Partner@{partner.region}123"
            test_accounts.append({
                "email": user.email,
                "password": password,
                "role": "fulfillment-partner",
                "name": partner.name,
            })

        # 인플루언서 계정 조회
        influencers = (
            db.query(User, Affiliate)
            .join(Affiliate, User.id == Affiliate.user_id)
            .filter(User.role == "influencer")
            .all()
        )

        for user, affiliate in influencers:
            # seeders.py 규칙: password = "test123456"
            test_accounts.append({
                "email": user.email,
                "password": "test123456",
                "role": "influencer",
                "name": affiliate.name,
            })

        return test_accounts

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"테스트 계정 조회 중 오류가 발생했습니다: {str(e)}",
            },
        )
