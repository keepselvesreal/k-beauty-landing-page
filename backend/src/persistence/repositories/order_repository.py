"""주문 관련 데이터 접근 계층"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import Order, OrderItem


class OrderRepository:
    """Order Repository"""

    @staticmethod
    def get_order_by_id(db: Session, order_id: UUID) -> Order:
        """ID로 주문 조회"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_order_by_number(db: Session, order_number: str) -> Order:
        """주문 번호로 조회"""
        return db.query(Order).filter(Order.order_number == order_number).first()

    @staticmethod
    def create_order(
        db: Session,
        order_number: str,
        customer_id: UUID,
        subtotal: Decimal,
        shipping_fee: Decimal,
        total_price: Decimal,
        payment_status: str = "pending",
    ) -> Order:
        """주문 생성"""
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_price=total_price,
            payment_status=payment_status,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def add_order_item(
        db: Session,
        order_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: Decimal,
    ) -> OrderItem:
        """주문 상품 추가"""
        order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
        )
        db.add(order_item)
        db.commit()
        db.refresh(order_item)
        return order_item

    @staticmethod
    def update_payment_status(
        db: Session,
        order_id: UUID,
        payment_status: str,
    ) -> Order:
        """주문 결제 상태 업데이트"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.payment_status = payment_status
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_shipping_status(
        db: Session,
        order_id: UUID,
        shipping_status: str,
    ) -> Order:
        """주문 배송 상태 업데이트"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.shipping_status = shipping_status
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_order_status(
        db: Session,
        order_id: UUID,
        status: str,
    ) -> Order:
        """주문 결제 상태 업데이트 (하위호환성)"""
        return OrderRepository.update_payment_status(db, order_id, status)

    @staticmethod
    def update_order_payment_info(
        db: Session,
        order_id: UUID,
        paypal_order_id: str,
    ) -> Order:
        """주문의 PayPal 주문 ID 저장"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.paypal_order_id = paypal_order_id
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_cancellation_status(
        db: Session,
        order_id: UUID,
        status: str,
        reason: str = None,
    ) -> Order:
        """주문 취소 상태 업데이트"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.cancellation_status = status
            order.cancellation_reason = reason
            order.cancellation_requested_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_refund_status(
        db: Session,
        order_id: UUID,
        status: str,
        reason: str = None,
    ) -> Order:
        """주문 환불 상태 업데이트"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.refund_status = status
            order.refund_reason = reason
            order.refund_requested_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
        return order
