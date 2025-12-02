"""인증 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....persistence.database import get_db
from ....workflow.services.authentication_service import AuthenticationService
from ....utils.auth import JWTTokenManager
from ....utils.exceptions import AuthenticationError
from ...schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth/fulfillment-partner", tags=["Authentication"])


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
