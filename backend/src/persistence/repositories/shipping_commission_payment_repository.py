"""배송 커미션 지급 관련 데이터 접근 계층"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import ShippingCommissionPayment, ShipmentAllocation, FulfillmentPartner


class ShippingCommissionPaymentRepository:
    """Shipping Commission Payment Repository"""

    @staticmethod
    def get_pending_commission_by_partner(
        db: Session,
        fulfillment_partner_id: UUID,
    ) -> Decimal:
        """
        배송담당자의 미정산 배송 커미션 합계

        배송 완료(shipped_status='completed')된 주문의 ShipmentAllocation에서
        해당 배송담당자의 shipping_commission 합산

        Args:
            db: 데이터베이스 세션
            fulfillment_partner_id: 배송담당자 ID

        Returns:
            미정산 배송 커미션 합계
        """
        from src.persistence.models import Order

        # 배송 완료된 주문의 ShipmentAllocation에서 해당 배송담당자 커미션 합산
        result = db.query(ShipmentAllocation).join(
            Order,
            ShipmentAllocation.order_id == Order.id
        ).filter(
            ShipmentAllocation.partner_id == fulfillment_partner_id,
            Order.shipping_status == "completed",
        ).with_entities(
            db.func.coalesce(db.func.sum(ShipmentAllocation.shipping_commission), 0)
        ).scalar()

        return Decimal(str(result or 0))

    @staticmethod
    def create_payment(
        db: Session,
        fulfillment_partner_id: UUID,
        amount: Decimal,
        payment_method: str = None,
    ) -> ShippingCommissionPayment:
        """배송 커미션 지급 기록 생성"""
        payment = ShippingCommissionPayment(
            fulfillment_partner_id=fulfillment_partner_id,
            amount=amount,
            payment_method=payment_method,
            status="pending",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_payment_by_id(
        db: Session,
        payment_id: UUID,
    ) -> ShippingCommissionPayment | None:
        """지급 기록 ID로 조회"""
        return db.query(ShippingCommissionPayment).filter(
            ShippingCommissionPayment.id == payment_id
        ).first()

    @staticmethod
    def get_payments_by_partner(
        db: Session,
        fulfillment_partner_id: UUID,
        status: str = None,
    ) -> list[ShippingCommissionPayment]:
        """배송담당자의 지급 기록 조회"""
        query = db.query(ShippingCommissionPayment).filter(
            ShippingCommissionPayment.fulfillment_partner_id == fulfillment_partner_id
        )

        if status:
            query = query.filter(ShippingCommissionPayment.status == status)

        return query.order_by(
            ShippingCommissionPayment.created_at.desc()
        ).all()

    @staticmethod
    def approve_payment(
        db: Session,
        payment_id: UUID,
    ) -> ShippingCommissionPayment:
        """지급 승인"""
        payment = db.query(ShippingCommissionPayment).filter(
            ShippingCommissionPayment.id == payment_id
        ).first()

        if payment:
            payment.status = "completed"
            from datetime import datetime
            payment.paid_at = datetime.utcnow()
            db.commit()
            db.refresh(payment)

        return payment

    @staticmethod
    def reject_payment(
        db: Session,
        payment_id: UUID,
    ) -> ShippingCommissionPayment:
        """지급 거절"""
        payment = db.query(ShippingCommissionPayment).filter(
            ShippingCommissionPayment.id == payment_id
        ).first()

        if payment:
            payment.status = "failed"
            db.commit()
            db.refresh(payment)

        return payment
