"""주문 관련 라우터"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.presentation.schemas.orders import CancellationRefundRequest, OrderCreate, OrderResponse
from src.workflow.exceptions import OrderException, EmailAuthenticationError
from src.workflow.services.order_service import OrderService
from src.infrastructure.external_services import PaymentService

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
    email: str = None,
    db: Session = Depends(get_db),
):
    """
    주문 조회

    Args:
        order_number: 주문 번호
        email: 이메일 (선택사항, 제공되면 검증)

    Returns:
        주문 정보

    Raises:
        404: 주문을 찾을 수 없음
        401: 이메일이 일치하지 않음
    """
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

    # 이메일이 제공된 경우 검증
    if email:
        try:
            if order.customer.email != email:
                raise EmailAuthenticationError(
                    code="EMAIL_MISMATCH",
                    message="이메일이 일치하지 않습니다.",
                )
        except EmailAuthenticationError as e:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": e.code,
                    "message": e.message,
                },
            )

    # customer 및 order_items 정보 포함
    return OrderResponse.model_validate(order)


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


@router.post("/{order_number}/cancel-request", response_model=OrderResponse)
async def request_cancellation(
    order_number: str,
    request_data: CancellationRefundRequest,
    db: Session = Depends(get_db),
):
    """
    주문 취소 요청

    조건:
    - shipping_status가 'shipped' 또는 'delivered'가 아니어야 함
    - cancellation_status가 'cancel_requested' 또는 'cancelled'가 아니어야 함
    """
    try:
        result = OrderService.request_cancellation(
            db,
            order_number=order_number,
            reason=request_data.reason,
        )
        return OrderResponse.model_validate(result["order"])
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


@router.post("/{order_number}/refund-request", response_model=OrderResponse)
async def request_refund(
    order_number: str,
    request_data: CancellationRefundRequest,
    db: Session = Depends(get_db),
):
    """
    주문 환불 요청

    조건:
    - shipping_status가 'delivered'여야 함
    - refund_status가 'refund_requested' 또는 'refunded'가 아니어야 함
    """
    try:
        result = OrderService.request_refund(
            db,
            order_number=order_number,
            reason=request_data.reason,
        )
        return OrderResponse.model_validate(result["order"])
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
