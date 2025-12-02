"""배송담당자 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.persistence.models import User, FulfillmentPartner
from src.persistence.repositories.order_repository import OrderRepository
from src.presentation.schemas.fulfillment_partner import (
    FulfillmentPartnerOrdersListResponse,
    FulfillmentPartnerOrderResponse,
    ProductInOrder,
)
from src.utils.auth import JWTTokenManager
from src.utils.exceptions import AuthenticationError

router = APIRouter(prefix="/api/fulfillment-partner", tags=["Fulfillment Partner"])


def get_current_fulfillment_partner(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> FulfillmentPartner:
    """
    현재 배송담당자 정보 추출

    Args:
        authorization: Authorization 헤더 (Bearer token)
        db: 데이터베이스 세션

    Returns:
        현재 사용자의 FulfillmentPartner 객체

    Raises:
        HTTPException: 토큰 없음, 유효하지 않음, 배송담당자 아님
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

    # 배송담당자 조회
    partner = user.fulfillment_partner
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_FULFILLMENT_PARTNER",
                "message": "배송담당자 권한이 필요합니다.",
            },
        )

    return partner


@router.get("/orders", response_model=FulfillmentPartnerOrdersListResponse)
async def get_fulfillment_partner_orders(
    current_partner: FulfillmentPartner = Depends(get_current_fulfillment_partner),
    db: Session = Depends(get_db),
):
    """
    배송담당자 주문 목록 조회

    조회 조건:
    - 본인 배송담당자에게만 할당된 주문
    - payment_status = 'completed' (결제 완료)
    - shipping_status = 'preparing' (배송 대기 중)
    - 생성 날짜 역순 정렬 (최신 먼저)

    Returns:
        {
            "partner_id": "uuid",
            "partner_name": "배송담당자명",
            "orders": [
                {
                    "order_id": "uuid",
                    "order_number": "ORD-xxx",
                    "customer_email": "customer@example.com",
                    "products": [
                        {
                            "name": "상품명",
                            "quantity": 5,
                            "unit_price": 1500.00
                        }
                    ],
                    "shipping_address": "배송주소",
                    "total_price": 1600.00,
                    "status": "preparing",
                    "created_at": "2025-12-02T15:30:00Z"
                }
            ]
        }
    """
    # 배송담당자의 주문 조회
    orders = OrderRepository.get_orders_by_fulfillment_partner(
        db,
        current_partner.id,
    )

    # 응답 데이터 구성
    orders_response = []
    for order in orders:
        # 상품 정보 추출
        products = [
            ProductInOrder(
                name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order.order_items
        ]

        # 배송주소: 고객의 address 또는 region
        shipping_address = order.customer.address or order.customer.region or "N/A"

        order_response = FulfillmentPartnerOrderResponse(
            order_id=order.id,
            order_number=order.order_number,
            customer_email=order.customer.email,
            products=products,
            shipping_address=shipping_address,
            total_price=order.total_price,
            status=order.shipping_status,
            created_at=order.created_at,
        )
        orders_response.append(order_response)

    return FulfillmentPartnerOrdersListResponse(
        partner_id=current_partner.id,
        partner_name=current_partner.name,
        orders=orders_response,
    )
