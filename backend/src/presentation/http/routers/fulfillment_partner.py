"""배송담당자 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.persistence.models import User, FulfillmentPartner, Order, Shipment
from src.persistence.repositories.order_repository import OrderRepository
from src.presentation.schemas.fulfillment_partner import (
    FulfillmentPartnerOrdersListResponse,
    FulfillmentPartnerOrderResponse,
    ProductInOrder,
    ShipmentRequest,
    ShipmentResponse,
)
from src.presentation.schemas.admin import CompleteShipmentResponse
from src.infrastructure.auth import JWTTokenManager
from src.infrastructure.exceptions import AuthenticationError
from src.workflow.exceptions import OrderException
from src.workflow.services.shipment_service import ShipmentService
from src.infrastructure.external_services import EmailService
from uuid import UUID

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
    - 모든 배송 상태의 주문 포함 (preparing, in_transit, shipped, delivered)
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

        order_response = FulfillmentPartnerOrderResponse(
            order_id=order.id,
            order_number=order.order_number,
            customer_name=order.customer.name,
            customer_email=order.customer.email,
            customer_region=order.customer.region,
            customer_address=order.customer.address or "N/A",
            customer_detailed_address=getattr(order.customer, 'detailed_address', None),
            products=products,
            total_price=order.total_price,
            status=order.shipping_status,
            created_at=order.created_at,
        )
        orders_response.append(order_response)

    return FulfillmentPartnerOrdersListResponse(
        partner_id=current_partner.id,
        partner_name=current_partner.name,
        partner_email=current_partner.email,
        orders=orders_response,
    )


@router.patch("/orders/{order_id}/ship", response_model=ShipmentResponse)
async def process_shipment(
    order_id: UUID,
    shipment_data: ShipmentRequest,
    current_partner: FulfillmentPartner = Depends(get_current_fulfillment_partner),
    db: Session = Depends(get_db),
):
    """
    배송 정보 입력 및 발송 완료 처리

    단계:
    1. ShipmentService.process_shipment() 호출
    2. Order 상태 업데이트 (preparing → shipped)
    3. Shipment 레코드 생성
    4. 배송 알림 이메일 발송
    5. 이메일 결과 응답에 포함

    Request:
    {
        "carrier": "LBC",
        "tracking_number": "1234567890"
    }

    Response:
    {
        "order_id": "uuid",
        "order_number": "ORD-001",
        "status": "shipped",
        "carrier": "LBC",
        "tracking_number": "1234567890",
        "shipped_at": "2025-12-02T15:45:00Z",
        "email_status": "sent" | "failed"
    }
    """
    try:
        # 1. 배송 정보 처리 (권한 검증 포함)
        result = ShipmentService.process_shipment(
            db,
            order_id=order_id,
            partner_id=current_partner.id,
            carrier=shipment_data.carrier,
            tracking_number=shipment_data.tracking_number,
        )

        # 2. 주문 객체 재조회 (이메일 발송용)
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise OrderException(
                code="ORDER_NOT_FOUND",
                message=f"주문을 찾을 수 없습니다: {order_id}",
            )

        # 3. 배송 알림 이메일 발송
        email_success = EmailService.send_shipment_notification(
            db,
            order=order,
            carrier=shipment_data.carrier,
            tracking_number=shipment_data.tracking_number,
        )

        # 4. 응답 반환
        return ShipmentResponse(
            order_id=result["order_id"],
            order_number=result["order_number"],
            status=result["status"],
            carrier=result["carrier"],
            tracking_number=result["tracking_number"],
            shipped_at=result["shipped_at"],
            email_status="sent" if email_success else "failed",
        )

    except AuthenticationError as e:
        # 권한 오류 (다른 배송담당자의 주문)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )

    except OrderException as e:
        # 주문 오류 (없음, 유효하지 않은 입력 등)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )


@router.patch("/orders/{order_id}/complete", response_model=CompleteShipmentResponse)
async def complete_delivery(
    order_id: UUID,
    current_partner: FulfillmentPartner = Depends(get_current_fulfillment_partner),
    db: Session = Depends(get_db),
):
    """
    배송 완료 처리 (고객이 배송받은 상태로 변경)

    단계:
    1. Order의 Shipment 조회
    2. 권한 검증 (본인 배송담당자의 배송만 처리)
    3. Shipment 상태 업데이트 (shipped → delivered)
    4. Order 상태 업데이트 (in_transit → delivered)
    5. delivered_at 타임스탬프 기록

    Args:
        order_id: 주문 ID

    Returns:
        {
            "success": True,
            "shipment_id": "uuid",
            "order_id": "uuid",
            "order_number": "ORD-xxx",
            "status": "delivered",
            "delivered_at": "2025-12-03T12:00:00Z"
        }
    """
    try:
        # 1. Order 확인 및 권한 검증
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise OrderException(
                code="ORDER_NOT_FOUND",
                message=f"주문을 찾을 수 없습니다: {order_id}",
            )

        if order.fulfillment_partner_id != current_partner.id:
            raise AuthenticationError(
                code="FORBIDDEN",
                message="이 주문을 처리할 권한이 없습니다.",
            )

        # 2. Shipment 조회
        shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
        if not shipment:
            # 배송 상태에 따른 명확한 에러 메시지 제공
            if order.shipping_status == "preparing":
                raise OrderException(
                    code="SHIPMENT_NOT_FOUND",
                    message="아직 배송 정보가 등록되지 않았습니다. 먼저 배송 정보를 입력한 후 배송 완료 처리가 가능합니다.",
                )
            elif order.shipping_status == "delivered":
                raise OrderException(
                    code="ALREADY_DELIVERED",
                    message="이미 배송 완료된 주문입니다.",
                )
            else:
                raise OrderException(
                    code="SHIPMENT_NOT_FOUND",
                    message=f"배송 정보를 찾을 수 없습니다. 현재 배송 상태: {order.shipping_status}",
                )

        # 3. 배송 완료 처리 (ShipmentService 활용)
        result = ShipmentService.complete_shipment(
            db,
            shipment_id=shipment.id,
            partner_id=current_partner.id,  # 권한 검증 포함
        )

        return CompleteShipmentResponse(
            success=result["success"],
            shipment_id=result["shipment_id"],
            order_id=result["order_id"],
            order_number=result["order_number"],
            status=result["status"],
            delivered_at=result["delivered_at"],
        )

    except AuthenticationError as e:
        # 권한 오류
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )

    except OrderException as e:
        # 주문 오류
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )
