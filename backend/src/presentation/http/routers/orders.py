"""주문 관련 라우터"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.presentation.schemas.orders import OrderCreate, OrderResponse
from src.utils.exceptions import OrderException
from src.workflow.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
):
    """
    주문 생성

    - 재고 확인 수행
    - 주문 번호 자동 생성
    - 배송료 자동 계산
    - 주문을 'pending' 상태로 저장
    """
    try:
        result = OrderService.create_order(
            db,
            customer_id=order_data.customer_id,
            product_id=order_data.product_id,
            quantity=order_data.quantity,
            region=order_data.region,
        )
        return result["order"]
    except OrderException as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e),
            },
        )


@router.get("/{order_number}", response_model=OrderResponse)
async def get_order(
    order_number: str,
    db: Session = Depends(get_db),
):
    """주문 조회"""
    from src.persistence.repositories.order_repository import OrderRepository

    order = OrderRepository.get_order_by_number(db, order_number)
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ORDER_NOT_FOUND",
                "message": f"주문을 찾을 수 없습니다: {order_number}",
            },
        )

    # customer 및 order_items 정보 포함
    return OrderResponse(
        **order.__dict__,
        customer=order.customer,
        order_items=order.order_items,
    )


@router.post("/{order_id}/initiate-payment")
async def initiate_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    PayPal 결제 초기화

    주문에 대한 PayPal 결제를 시작하고 승인 URL 반환

    Returns:
        {
            "paypal_order_id": str,
            "approval_url": str
        }
    """
    from uuid import UUID

    try:
        # UUID로 변환
        order_uuid = UUID(order_id)

        result = OrderService.initiate_payment(db, order_uuid)
        return {
            "paypal_order_id": result["paypal_order_id"],
            "approval_url": result["approval_url"],
        }
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_ORDER_ID",
                "message": "유효하지 않은 주문 ID 형식입니다.",
            },
        )
    except OrderException as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e),
            },
        )
