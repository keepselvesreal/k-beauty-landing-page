"""PayPal Order 생성 통합 테스트"""

import pytest
from decimal import Decimal
from unittest.mock import patch, Mock

from src.workflow.services.order_service import OrderService
from src.infrastructure.external_services import PaymentService
from src.workflow.exceptions import PaymentProcessingError


class TestPayPalOrderCreation:
    """PayPal Order 생성 통합 테스트"""

    def test_create_order_and_initiate_payment_success(self, client, complete_test_data):
        """
        **TC-3.4.1: Order 생성 및 PayPal 결제 초기화 성공** 🟢 Happy Path 🟠 Integration

        Given: 주문 정보와 결제 정보가 준비됨
        When: Order 생성 후 PayPal Order 생성 시도
        Then:
          - Order가 pending_payment 상태로 생성
          - paypal_order_id가 저장됨
          - approval_url이 반환됨
        """
        data = complete_test_data
        db = data["db"]

        # 1단계: Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=5,
            region="NCR",
        )

        order = order_result["order"]
        assert order.payment_status == "pending", "초기 주문 상태는 pending이어야 함"
        assert order.paypal_order_id is None, "아직 PayPal Order ID가 없어야 함"

        # 2단계: PayPal Order 생성
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-INTEGRATION-TEST-001"
            mock_payment.state = "created"
            mock_payment.links = [
                {'rel': 'approval_url', 'href': 'https://www.sandbox.paypal.com/checkoutnow?token=TEST'},
            ]
            mock_payment_class.return_value = mock_payment

            # PayPal 결제 시작
            payment_result = OrderService.initiate_payment(db, order.id)

            # 검증
            assert payment_result["paypal_order_id"] == "PAYID-INTEGRATION-TEST-001"
            assert "approval_url" in payment_result
            assert payment_result["approval_url"].startswith("https://")

            # Order 상태 확인
            updated_order = payment_result["order"]
            assert updated_order.paypal_order_id == "PAYID-INTEGRATION-TEST-001"

    def test_initiate_payment_order_not_found(self, client, complete_test_data):
        """
        **TC-3.4.2: PayPal 결제 초기화 실패 - 주문 없음** 🔴 Error Case 🟠 Integration

        Given: 존재하지 않는 주문 ID
        When: OrderService.initiate_payment() 호출
        Then: OrderException 예외 발생
        """
        from uuid import uuid4
        from src.workflow.exceptions import OrderException

        db = complete_test_data["db"]

        with pytest.raises(OrderException) as exc_info:
            OrderService.initiate_payment(db, uuid4())

        assert exc_info.value.code == "ORDER_NOT_FOUND"

    def test_initiate_payment_paypal_failure(self, client, complete_test_data):
        """
        **TC-3.4.3: PayPal 결제 초기화 실패 - PayPal API 에러** 🔴 Error Case 🟠 Integration

        Given: 유효한 주문, PayPal API 실패
        When: OrderService.initiate_payment() 호출
        Then:
          - PaymentProcessingError 예외 발생
          - Order 상태가 payment_failed로 업데이트됨
        """
        data = complete_test_data
        db = data["db"]

        # Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=5,
            region="NCR",
        )
        order = order_result["order"]

        # PayPal API 실패 Mock
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = False
            mock_payment.error = {
                'name': 'VALIDATION_ERROR',
                'message': 'Invalid request'
            }
            mock_payment_class.return_value = mock_payment

            # PayPal 결제 시작 시도
            with pytest.raises(PaymentProcessingError):
                OrderService.initiate_payment(db, order.id)

            # Order 상태 확인
            from src.persistence.repositories.order_repository import OrderRepository
            updated_order = OrderRepository.get_order_by_id(db, order.id)
            assert updated_order.payment_status == "payment_failed", "주문 상태가 payment_failed로 업데이트되어야 함"

    def test_total_order_flow_with_payment(self, client, complete_test_data):
        """
        **TC-3.4.4: 전체 주문 흐름 (Order 생성 → PayPal 결제)** 🟢 Happy Path 🟠 Integration

        Given: 완전한 테스트 데이터
        When: Order 생성 후 PayPal 결제 초기화
        Then:
          - Order가 생성되고
          - PayPal Order ID가 저장되고
          - Approval URL이 반환됨
        """
        data = complete_test_data
        db = data["db"]

        # Step 1: Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=3,
            region="Luzon",
        )
        order = order_result["order"]

        # 검증: Order 정보
        assert order.order_number.startswith("ORD-")
        assert order.subtotal == Decimal("150.00")  # 50 * 3
        assert order.shipping_fee == Decimal("120.00")  # Luzon
        assert order.total_price == Decimal("270.00")
        assert order.payment_status == "pending"

        # Step 2: PayPal 결제 초기화
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-FLOW-TEST-001"
            mock_payment.state = "created"
            mock_payment.links = [
                {'rel': 'approval_url', 'href': 'https://www.sandbox.paypal.com/checkoutnow?token=FLOW'},
            ]
            mock_payment_class.return_value = mock_payment

            payment_result = OrderService.initiate_payment(db, order.id)

            # 검증: Payment 결과
            assert payment_result["paypal_order_id"] == "PAYID-FLOW-TEST-001"
            assert "FLOW" in payment_result["approval_url"]

            # 검증: Order 상태 업데이트
            from src.persistence.repositories.order_repository import OrderRepository
            final_order = OrderRepository.get_order_by_id(db, order.id)
            assert final_order.paypal_order_id == "PAYID-FLOW-TEST-001"

        print(f"\n✅ 전체 주문 흐름 검증 완료")
        print(f"  - Order: {order.order_number}")
        print(f"  - Total: ₱{order.total_price}")
        print(f"  - PayPal Order ID: {payment_result['paypal_order_id']}")
