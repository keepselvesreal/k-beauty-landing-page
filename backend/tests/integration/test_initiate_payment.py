"""PayPal 결제 초기화 엔드포인트 통합 테스트"""

import pytest
from decimal import Decimal
from unittest.mock import patch, Mock
from uuid import uuid4

from src.workflow.exceptions import PaymentProcessingError


class TestInitiatePayment:
    """PayPal 결제 초기화 엔드포인트 테스트"""

    def test_initiate_payment_success(self, client, complete_test_data):
        """
        **TC-3.5.1: PayPal 결제 초기화 성공** 🟢 Happy Path 🟠 Integration
        """
        # ========== GIVEN ==========
        # 유효한 주문이 생성되어 있음 (payment_status="pending")
        data = complete_test_data
        db = data["db"]

        from src.workflow.services.order_service import OrderService

        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=2,
            region="NCR",
        )
        order = order_result["order"]

        assert order.payment_status == "pending"
        assert order.paypal_order_id is None

        # ========== WHEN ==========
        # POST /api/orders/{order_id}/initiate-payment 호출
        with patch("src.workflow.services.payment_service.paypalrestsdk.Payment") as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-SUCCESS-001"
            mock_payment.links = [
                {"rel": "approval_url", "href": "https://www.sandbox.paypal.com/checkoutnow?token=EC-001"}
            ]
            mock_payment_class.return_value = mock_payment

            response = client.post(f"/api/orders/{order.id}/initiate-payment")

        # ========== THEN ==========
        # Status 200, paypal_order_id와 approval_url 반환, order.paypal_order_id 저장됨
        assert response.status_code == 200
        result = response.json()

        assert result["paypal_order_id"] == "PAYID-SUCCESS-001"
        assert "approval_url" in result
        assert "checkoutnow" in result["approval_url"]

        # DB에서 order 다시 조회해서 paypal_order_id 저장됐는지 확인
        from src.persistence.repositories.order_repository import OrderRepository

        updated_order = OrderRepository.get_order_by_id(db, order.id)
        assert updated_order.paypal_order_id == "PAYID-SUCCESS-001"

    def test_initiate_payment_invalid_order_id_format(self, client):
        """
        **TC-3.5.2: 잘못된 order_id 형식** 🔴 Error Case 🟠 Integration
        """
        # ========== GIVEN ==========
        # 잘못된 order_id (UUID 형식 아님)
        invalid_id = "not-a-uuid"

        # ========== WHEN ==========
        # POST /api/orders/{invalid-id}/initiate-payment 호출
        response = client.post(f"/api/orders/{invalid_id}/initiate-payment")

        # ========== THEN ==========
        # Status 400, INVALID_ORDER_ID 에러 코드
        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["code"] == "INVALID_ORDER_ID"
        assert "유효하지 않은 주문 ID" in result["detail"]["message"]

    def test_initiate_payment_order_not_found(self, client):
        """
        **TC-3.5.3: 존재하지 않는 주문** 🔴 Error Case 🟠 Integration
        """
        # ========== GIVEN ==========
        # 유효한 UUID 형식이지만 DB에 없는 order_id
        non_existent_id = str(uuid4())

        # ========== WHEN ==========
        # POST /api/orders/{non-existent-uuid}/initiate-payment 호출
        response = client.post(f"/api/orders/{non_existent_id}/initiate-payment")

        # ========== THEN ==========
        # Status 400, ORDER_NOT_FOUND 에러 코드
        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["code"] == "ORDER_NOT_FOUND"

    def test_initiate_payment_paypal_api_failure(self, client, complete_test_data):
        """
        **TC-3.5.4: PayPal API 실패 처리** 🔴 Error Case 🟠 Integration
        """
        # ========== GIVEN ==========
        # 유효한 주문이 생성되어 있음 (payment_status="pending")
        # PayPal API가 실패 상황 (모킹)
        data = complete_test_data
        db = data["db"]

        from src.workflow.services.order_service import OrderService

        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=1,
            region="NCR",
        )
        order = order_result["order"]

        assert order.payment_status == "pending"

        # ========== WHEN ==========
        # POST /api/orders/{order_id}/initiate-payment 호출 (PayPal API 실패 시뮬레이션)
        with patch("src.workflow.services.payment_service.paypalrestsdk.Payment") as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = False
            mock_payment.error = {"name": "VALIDATION_ERROR", "message": "Invalid request"}
            mock_payment_class.return_value = mock_payment

            response = client.post(f"/api/orders/{order.id}/initiate-payment")

        # ========== THEN ==========
        # Status 400 또는 500 반환
        # order.payment_status가 "payment_failed"로 변경됨
        assert response.status_code in [400, 500]
        result = response.json()
        assert "detail" in result

        # DB에서 order 다시 조회해서 payment_status 확인
        from src.persistence.repositories.order_repository import OrderRepository

        updated_order = OrderRepository.get_order_by_id(db, order.id)
        assert updated_order.payment_status == "payment_failed", (
            "PayPal 실패 시 주문 상태가 payment_failed로 변경되어야 함"
        )
