"""관리자 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....persistence.database import get_db
from ....workflow.services.admin_service import AdminService
from ....utils.exceptions import AuthenticationError
from ...schemas.admin import CreateUserRequest, CreateUserResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.post("/users", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
):
    """사용자 생성 (배송담당자, 인플루언서)"""
    try:
        # Service 계층에서 사용자 생성
        user = AdminService.create_user(
            db,
            email=request.email,
            password=request.password,
            role=request.role,
        )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
