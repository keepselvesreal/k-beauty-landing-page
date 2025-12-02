"""주문 비즈니스 로직 서비스"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.persistence.repositories.customer_repository import CustomerRepository
from src.persistence.repositories.inventory_repository import InventoryRepository
from src.persistence.repositories.order_repository import OrderRepository
from src.persistence.repositories.product_repository import ProductRepository
from src.persistence.repositories.shipping_repository import ShippingRepository
from src.utils.exceptions import OrderException, PaymentProcessingError
from src.workflow.services.payment_service import PaymentService


class OrderService:
    """Order Service - 주문 생성 및 검증"""

    @staticmethod
    def generate_order_number() -> str:
        """주문 번호 생성 (ORD-{UUID} 형식)"""
        return f"ORD-{uuid4()}"

    @staticmethod
    def create_order(
        db: Session,
        customer_id: UUID,
        product_id: UUID,
        quantity: int,
        region: str,
    ) -> dict:
        """
        주문 생성

        Args:
            db: 데이터베이스 세션
            customer_id: 고객 ID
            product_id: 상품 ID
            quantity: 주문 수량
            region: 배송 지역 (NCR, Luzon, Visayas, Mindanao)

        Returns:
            생성된 주문 정보 딕셔너리

        Raises:
            OrderException: 고객/상품 없음, 재고 부족 등
        """

        # 1. 고객 확인
        customer = CustomerRepository.get_customer_by_id(db, customer_id)
        if not customer:
            raise OrderException(code="CUSTOMER_NOT_FOUND", message="고객을 찾을 수 없습니다.")

        # 2. 상품 확인
        product = ProductRepository.get_product_by_id(db, product_id)
        if not product:
            raise OrderException(code="PRODUCT_NOT_FOUND", message="상품을 찾을 수 없습니다.")

        # 3. 재고 확인
        is_available = InventoryRepository.check_inventory_available(db, product_id, quantity)
        if not is_available:
            raise OrderException(
                code="INSUFFICIENT_STOCK",
                message=f"재고가 부족합니다. 요청: {quantity}개",
            )

        # 4. 배송료 조회
        shipping_rate = ShippingRepository.get_shipping_rate_by_region(db, region)
        if not shipping_rate:
            raise OrderException(
                code="INVALID_REGION",
                message=f"유효하지 않은 지역입니다: {region}",
            )

        # 5. 가격 계산
        unit_price = Decimal(str(product.price))
        subtotal = unit_price * quantity
        shipping_fee = Decimal(str(shipping_rate.fee))
        total_price = subtotal + shipping_fee

        # 6. 주문 생성
        order_number = OrderService.generate_order_number()
        order = OrderRepository.create_order(
            db,
            order_number=order_number,
            customer_id=customer_id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_price=total_price,
            payment_status="pending",
        )

        # 7. 주문 상품 추가
        order_item = OrderRepository.add_order_item(
            db,
            order_id=order.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
        )

        return {
            "order": order,
            "order_item": order_item,
            "product": product,
            "customer": customer,
        }

    @staticmethod
    def initiate_payment(
        db: Session,
        order_id: UUID,
    ) -> dict:
        """
        주문에 대한 PayPal 결제 시작

        Args:
            db: 데이터베이스 세션
            order_id: 주문 ID

        Returns:
            {
                "order": Order,
                "paypal_order_id": str,
                "approval_url": str,
            }

        Raises:
            OrderException: 주문 없음
            PaymentProcessingError: PayPal 결제 실패
        """
        # 1. 주문 확인
        order = OrderRepository.get_order_by_id(db, order_id)
        if not order:
            raise OrderException(code="ORDER_NOT_FOUND", message="주문을 찾을 수 없습니다.")

        try:
            # 2. PayPal Order 생성
            payment_result = PaymentService.create_paypal_order(
                amount=order.total_price,
                currency="PHP",
                description=f"Order {order.order_number}",
            )

            # 3. PayPal Order ID 저장
            OrderRepository.update_order_payment_info(
                db,
                order_id=order_id,
                paypal_order_id=payment_result["paypal_order_id"],
            )

            return {
                "order": order,
                "paypal_order_id": payment_result["paypal_order_id"],
                "approval_url": payment_result["approval_url"],
            }

        except PaymentProcessingError:
            # 결제 생성 실패 → 주문 상태를 payment_failed로 업데이트
            OrderRepository.update_order_status(db, order_id, "payment_failed")
            raise

    @staticmethod
    def request_cancellation(
        db: Session,
        order_number: str,
        reason: str,
    ) -> dict:
        """
        주문 취소 요청

        조건:
        - shipping_status가 'shipped' 또는 'delivered'가 아니어야 함
        - cancellation_status가 'cancel_requested' 또는 'cancelled'가 아니어야 함

        Args:
            db: 데이터베이스 세션
            order_number: 주문 번호
            reason: 취소 사유

        Returns:
            {"order": Order}

        Raises:
            OrderException: 주문 없음, 상태 불가 등
        """
        # 1. 주문 확인
        order = OrderRepository.get_order_by_number(db, order_number)
        if not order:
            raise OrderException(code="ORDER_NOT_FOUND", message="주문을 찾을 수 없습니다.")

        # 2. 취소 가능 상태 검증
        if order.shipping_status in ["shipped", "delivered"]:
            raise OrderException(
                code="CANCELLATION_NOT_ALLOWED",
                message="배송 후에는 취소할 수 없습니다.",
            )

        # 3. 중복 요청 방지
        if order.cancellation_status in ["cancel_requested", "cancelled"]:
            raise OrderException(
                code="DUPLICATE_CANCELLATION_REQUEST",
                message="이미 취소 요청이 진행 중이거나 취소된 주문입니다.",
            )

        # 4. 취소 상태 업데이트
        updated_order = OrderRepository.update_cancellation_status(
            db,
            order_id=order.id,
            status="cancel_requested",
            reason=reason,
        )

        return {"order": updated_order}

    @staticmethod
    def request_refund(
        db: Session,
        order_number: str,
        reason: str,
    ) -> dict:
        """
        주문 환불 요청

        조건:
        - shipping_status가 'delivered'여야 함
        - refund_status가 'refund_requested' 또는 'refunded'가 아니어야 함

        Args:
            db: 데이터베이스 세션
            order_number: 주문 번호
            reason: 환불 사유

        Returns:
            {"order": Order}

        Raises:
            OrderException: 주문 없음, 상태 불가 등
        """
        # 1. 주문 확인
        order = OrderRepository.get_order_by_number(db, order_number)
        if not order:
            raise OrderException(code="ORDER_NOT_FOUND", message="주문을 찾을 수 없습니다.")

        # 2. 환불 가능 상태 검증
        if order.shipping_status != "delivered":
            raise OrderException(
                code="REFUND_NOT_ALLOWED",
                message="배송 완료 후에만 환불을 요청할 수 있습니다.",
            )

        # 3. 중복 요청 방지
        if order.refund_status in ["refund_requested", "refunded"]:
            raise OrderException(
                code="DUPLICATE_REFUND_REQUEST",
                message="이미 환불 요청이 진행 중이거나 환불된 주문입니다.",
            )

        # 4. 환불 상태 업데이트
        updated_order = OrderRepository.update_refund_status(
            db,
            order_id=order.id,
            status="refund_requested",
            reason=reason,
        )

        return {"order": updated_order}
