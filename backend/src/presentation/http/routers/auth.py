"""인증 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ....persistence.database import get_db
from ....persistence.models import User
from ....workflow.services.authentication_service import AuthenticationService
from ....utils.auth import JWTTokenManager
from ....utils.exceptions import AuthenticationError
from ...schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth/fulfillment-partner", tags=["Authentication"])


class CurrentUserResponse(BaseModel):
    """현재 사용자 정보 응답"""
    user_id: str
    email: str
    role: str


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """현재 사용자 정보 추출 (의존성)"""
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
async def login_fulfillment_partner(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """배송담당자 로그인"""
    try:
        # Service 계층에서 인증 처리
        user = AuthenticationService.authenticate_user_by_email(
            db,
            email=credentials.email,
            password=credentials.password,
        )

        # 토큰 생성
        token_payload = {
            "user_id": str(user.id),
            "role": user.role.value,
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
    current_user: User = Depends(get_current_user),
):
    """현재 사용자 정보 조회"""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
    }
