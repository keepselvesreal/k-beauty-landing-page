"""Order Service 테스트"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.persistence.models import Order
from src.utils.exceptions import OrderException
from src.workflow.services.order_service import OrderService


class TestRequestCancellation:
    """주문 취소 요청"""

    def test_request_cancellation_success_before_shipping(
        self,
        test_db: Session,
        order_with_customer: Order,
    ):
        """TC-1.1.1: 배송 시작 전 주문 취소 요청 🟢 Happy Path"""
        # Given (order_with_customer는 이미 shipping_status="preparing"으로 생성됨)
        assert order_with_customer.shipping_status == "preparing"
        assert order_with_customer.cancellation_status is None

        # When
        result = OrderService.request_cancellation(
            test_db,
            order_number=order_with_customer.order_number,
            reason="Wrong size",
        )

        # Then
        assert result["order"].cancellation_status == "cancel_requested"
        assert result["order"].cancellation_reason == "Wrong size"
        assert result["order"].cancellation_requested_at is not None

        # DB에서도 확인
        test_db.refresh(order_with_customer)
        assert order_with_customer.cancellation_status == "cancel_requested"
        assert order_with_customer.cancellation_reason == "Wrong size"


class TestRequestRefund:
    """주문 환불 요청"""

    def test_request_refund_success_after_delivery(
        self,
        test_db: Session,
        order_with_customer_delivered: Order,
    ):
        """TC-1.2.1: 배송 완료 후 환불 요청 🟢 Happy Path"""
        # Given (order_with_customer_delivered는 이미 shipping_status="delivered"로 생성됨)
        assert order_with_customer_delivered.shipping_status == "delivered"
        assert order_with_customer_delivered.refund_status is None

        # When
        result = OrderService.request_refund(
            test_db,
            order_number=order_with_customer_delivered.order_number,
            reason="Defective product",
        )

        # Then
        assert result["order"].refund_status == "refund_requested"
        assert result["order"].refund_reason == "Defective product"
        assert result["order"].refund_requested_at is not None

        # DB에서도 확인
        test_db.refresh(order_with_customer_delivered)
        assert order_with_customer_delivered.refund_status == "refund_requested"
        assert order_with_customer_delivered.refund_reason == "Defective product"
