"""관리자 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from uuid import UUID

from ....persistence.database import get_db
from ....persistence.models import User
from ....persistence.repositories.inventory_repository import InventoryRepository
from ....workflow.services.admin_service import AdminService
from ....utils.auth import JWTTokenManager
from ....utils.exceptions import AuthenticationError, OrderException
from ...schemas.admin import (
    CreateUserRequest,
    CreateUserResponse,
    AdjustInventoryRequest,
    AdjustInventoryResponse,
    InventoryListResponse,
    InventoryHistoryResponse,
    InventoryItem,
    InventoryAdjustmentHistoryItem,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def get_current_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    현재 관리자 인증 확인

    Args:
        authorization: Authorization 헤더 (Bearer token)
        db: 데이터베이스 세션

    Returns:
        현재 사용자의 User 객체 (role == "admin")

    Raises:
        HTTPException: 토큰 없음, 유효하지 않음, 관리자 아님
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

    # 관리자 역할 확인
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_ADMIN",
                "message": "관리자 권한이 필요합니다.",
            },
        )

    return user


@router.post("/users", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """사용자 생성 (배송담당자, 인플루언서) - 관리자 전용"""
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


# ============================================
# 재고 관리 엔드포인트
# ============================================

@router.get("/inventory", response_model=InventoryListResponse)
async def get_inventory(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    모든 배송담당자의 재고 목록 조회

    Returns:
        - inventories: 재고 목록 (배송담당자명, 상품명, 현재 수량 등)
        - total_count: 전체 재고 항목 수
    """
    try:
        inventories = InventoryRepository.get_all_inventory_by_admin(db)

        return {
            "inventories": [InventoryItem(**item) for item in inventories],
            "total_count": len(inventories),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INVENTORY_FETCH_FAILED",
                "message": f"재고 조회에 실패했습니다: {str(e)}",
            },
        )


@router.put("/inventory/{inventory_id}", response_model=AdjustInventoryResponse)
async def adjust_inventory(
    inventory_id: UUID,
    request: AdjustInventoryRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    특정 배송담당자의 재고 수량 조정

    Args:
        inventory_id: PartnerAllocatedInventory ID
        request: 새 수량과 조정 사유

    Returns:
        조정 결과 (이전 수량, 새 수량, 이력 ID 등)
    """
    try:
        result = InventoryRepository.adjust_inventory(
            db,
            inventory_id=inventory_id,
            new_quantity=request.new_quantity,
            admin_id=current_admin.id,
            reason=request.reason,
        )

        return AdjustInventoryResponse(
            inventory_id=result["inventory_id"],
            old_quantity=result["old_quantity"],
            new_quantity=result["new_quantity"],
            log_id=result["log_id"],
            updated_at=result["updated_at"],
        )

    except OrderException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INVENTORY_ADJUST_FAILED",
                "message": f"재고 조정에 실패했습니다: {str(e)}",
            },
        )


@router.get("/inventory/{inventory_id}/history", response_model=InventoryHistoryResponse)
async def get_inventory_history(
    inventory_id: UUID,
    limit: int = 10,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    특정 재고의 조정 이력 조회

    Args:
        inventory_id: PartnerAllocatedInventory ID
        limit: 조회할 이력 건수 (기본값 10)

    Returns:
        재고 조정 이력 목록 (날짜, 이전/현재 수량, 사유 등)
    """
    try:
        history_logs = InventoryRepository.get_inventory_adjustment_history(
            db,
            inventory_id=inventory_id,
            limit=limit,
        )

        if not history_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "INVENTORY_NOT_FOUND",
                    "message": "해당 재고를 찾을 수 없습니다.",
                },
            )

        # 첫 번째 이력에서 재고 정보 조회
        from ....persistence.models import PartnerAllocatedInventory

        inventory = db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.id == inventory_id
        ).first()

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "INVENTORY_NOT_FOUND",
                    "message": "해당 재고를 찾을 수 없습니다.",
                },
            )

        partner_name = inventory.partner.name if inventory.partner else "Unknown"
        product_name = inventory.product.name if inventory.product else "Unknown"

        return InventoryHistoryResponse(
            inventory_id=inventory_id,
            partner_name=partner_name,
            product_name=product_name,
            history=[InventoryAdjustmentHistoryItem(**log) for log in history_logs],
        )

    except OrderException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INVENTORY_HISTORY_FETCH_FAILED",
                "message": f"이력 조회에 실패했습니다: {str(e)}",
            },
        )
