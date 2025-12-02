"""배송 처리 비즈니스 로직"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import Order, Shipment
from src.utils.exceptions import OrderException, AuthenticationError


class ShipmentService:
    """배송 처리 서비스"""

    @staticmethod
    def process_shipment(
        db: Session,
        order_id: UUID,
        partner_id: UUID,
        carrier: str,
        tracking_number: str,
    ) -> dict:
        """
        배송 정보 처리

        단계:
        1. 주문 조회 및 권한 검증
        2. 운송장 정보 검증
        3. Shipment 레코드 생성 또는 업데이트
        4. Order 상태 업데이트 (preparing → shipped)
        5. shipped_at 타임스탬프 기록

        Args:
            db: 데이터베이스 세션
            order_id: 주문 ID
            partner_id: 배송담당자 ID
            carrier: 택배사
            tracking_number: 운송장 번호

        Returns:
            {
                "success": True,
                "order_id": UUID,
                "order_number": str,
                "status": "shipped",
                "carrier": str,
                "tracking_number": str,
                "shipped_at": datetime,
            }

        Raises:
            OrderException: 주문 없음, 권한 없음, 검증 오류
        """

        # 1. 주문 조회
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise OrderException(
                code="ORDER_NOT_FOUND",
                message=f"주문을 찾을 수 없습니다: {order_id}",
            )

        # 2. 권한 검증 (본인 배송담당자의 주문인지 확인)
        if order.fulfillment_partner_id != partner_id:
            raise AuthenticationError(
                code="FORBIDDEN",
                message="이 주문을 처리할 권한이 없습니다.",
            )

        # 3. 택배사 & 운송장 번호 검증
        if not carrier or not carrier.strip():
            raise OrderException(
                code="INVALID_CARRIER",
                message="택배사는 필수입니다.",
            )

        if not tracking_number or not tracking_number.strip():
            raise OrderException(
                code="INVALID_TRACKING_NUMBER",
                message="운송장 번호는 필수입니다.",
            )

        # 4. Shipment 레코드 생성
        shipped_at = datetime.utcnow()

        shipment = Shipment(
            order_id=order.id,
            partner_id=partner_id,
            carrier=carrier.strip(),
            tracking_number=tracking_number.strip(),
            status="shipped",
            shipped_at=shipped_at,
        )
        db.add(shipment)

        # 5. Order 상태 업데이트
        order.shipping_status = "shipped"
        order.shipped_at = shipped_at
        db.add(order)

        db.commit()

        return {
            "success": True,
            "order_id": order.id,
            "order_number": order.order_number,
            "status": "shipped",
            "carrier": carrier.strip(),
            "tracking_number": tracking_number.strip(),
            "shipped_at": shipped_at,
        }
