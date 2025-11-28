"""PayPal Consumer Contract Test - 우리가 PayPal API에서 기대하는 응답 정의"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from src.workflow.services.payment_service import PaymentService
from src.utils.exceptions import PaymentProcessingError


class TestPayPalConsumer:
    """PayPal Consumer 측 계약 정의"""

    def test_paypal_order_creation_success(self):
        """
        **TC-3.1.Consumer.1: PayPal Order 생성 성공** 🟢 Happy Path 🔵 Unit

        Given: 유효한 주문 정보 (금액 750 PHP, 배송료 100 PHP)
        When: PaymentService.create_paypal_order() 호출
        Then: paypal_order_id와 approval_url이 반환되어야 함
        """
        # Given: Mock PayPal SDK
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            # PayPal 성공 응답 Mock
            mock_payment = Mock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-TEST123456789"
            mock_payment.state = "created"
            mock_payment.links = [
                {'rel': 'approval_url', 'href': 'https://www.sandbox.paypal.com/checkoutnow?token=TEST'},
                {'rel': 'execute', 'href': 'https://api.sandbox.paypal.com/v1/payments/payment/PAYID-TEST123456789/execute'},
            ]
            mock_payment_class.return_value = mock_payment

            # When: PaymentService.create_paypal_order() 호출
            result = PaymentService.create_paypal_order(
                amount=Decimal("750.00"),
                currency="PHP",
                description="K-Beauty Test Order"
            )

            # Then: 응답 검증
            assert result is not None, "Result는 None이 아니어야 함"
            assert result["success"] is True, "Success는 True여야 함"
            assert result["paypal_order_id"] == "PAYID-TEST123456789", "PayPal Order ID 미일치"
            assert "approval_url" in result, "Approval URL 없음"
            assert result["approval_url"].startswith("https://www.sandbox.paypal.com"), "Approval URL 형식 오류"

    def test_paypal_order_creation_invalid_amount_error(self):
        """
        **TC-3.1.Consumer.2: PayPal Order 생성 실패 - 유효하지 않은 금액** 🔴 Error Case 🔵 Unit

        Given: 유효하지 않은 금액 (0.00)
        When: PaymentService.create_paypal_order() 호출
        Then: PaymentProcessingError 예외 발생, 에러 메시지 포함
        """
        # Given: Mock PayPal SDK (실패 응답)
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = False
            mock_payment.error = {
                'name': 'VALIDATION_ERROR',
                'message': 'Invalid request - see details',
                'details': [
                    {'field': 'transactions[0].amount', 'issue': 'Amount cannot be zero'}
                ]
            }
            mock_payment_class.return_value = mock_payment

            # When & Then: PaymentProcessingError 예외 발생
            with pytest.raises(PaymentProcessingError) as exc_info:
                PaymentService.create_paypal_order(
                    amount=Decimal("0.00"),
                    currency="PHP",
                    description="Invalid Amount Test"
                )

            # 에러 메시지 검증
            assert "VALIDATION_ERROR" in str(exc_info.value)

    def test_paypal_order_creation_invalid_currency_error(self):
        """
        **TC-3.1.Consumer.3: PayPal Order 생성 실패 - 유효하지 않은 통화** 🔴 Error Case 🔵 Unit

        Given: 지원하지 않는 통화 코드 (INVALID)
        When: PaymentService.create_paypal_order() 호출
        Then: PaymentProcessingError 예외 발생, 에러 메시지 포함
        """
        # Given: Mock PayPal SDK (실패 응답)
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = False
            mock_payment.error = {
                'name': 'VALIDATION_ERROR',
                'message': 'Invalid request - see details',
                'details': [
                    {'field': 'transactions[0].amount.currency', 'issue': 'CURRENCY_NOT_SUPPORTED'}
                ]
            }
            mock_payment_class.return_value = mock_payment

            # When & Then: PaymentProcessingError 예외 발생
            with pytest.raises(PaymentProcessingError):
                PaymentService.create_paypal_order(
                    amount=Decimal("750.00"),
                    currency="INVALID",
                    description="Invalid Currency Test"
                )

    def test_paypal_order_response_structure(self):
        """
        **TC-3.1.Consumer.4: PayPal Order 응답 구조** 🟨 Edge Case 🔵 Unit

        Given: PayPal Order 생성 성공
        When: 응답 데이터 확인
        Then: 필수 필드들이 모두 포함되어야 함
              - success: bool
              - paypal_order_id: str (PAYID-로 시작)
              - approval_url: str (https://로 시작)
        """
        # Given: Mock PayPal SDK
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = Mock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-12345ABCDE"
            mock_payment.state = "created"
            mock_payment.links = [
                {'rel': 'approval_url', 'href': 'https://www.sandbox.paypal.com/checkoutnow?token=ABC123'},
            ]
            mock_payment_class.return_value = mock_payment

            # When: PaymentService.create_paypal_order() 호출
            result = PaymentService.create_paypal_order(
                amount=Decimal("750.00"),
                currency="PHP",
                description="Response Structure Test"
            )

            # Then: 응답 구조 검증
            assert isinstance(result, dict), "Result는 dict이어야 함"
            assert "success" in result, "success 필드 없음"
            assert "paypal_order_id" in result, "paypal_order_id 필드 없음"
            assert "approval_url" in result, "approval_url 필드 없음"

            # 필드 타입 검증
            assert isinstance(result["success"], bool), "success는 bool이어야 함"
            assert isinstance(result["paypal_order_id"], str), "paypal_order_id는 str이어야 함"
            assert isinstance(result["approval_url"], str), "approval_url은 str이어야 함"

            # 필드 값 형식 검증
            assert result["paypal_order_id"].startswith("PAYID-"), "paypal_order_id는 PAYID-로 시작해야 함"
            assert result["approval_url"].startswith("https://"), "approval_url은 https://로 시작해야 함"

    def test_paypal_network_error(self):
        """
        **TC-3.1.Consumer.5: PayPal 네트워크 에러** 🔴 Error Case 🔵 Unit

        Given: PayPal API가 네트워크 에러 (연결 불가)
        When: PaymentService.create_paypal_order() 호출
        Then: PaymentProcessingError 예외 발생
        """
        # Given: Mock PayPal SDK (네트워크 에러)
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment_class.side_effect = ConnectionError("Connection refused")

            # When & Then: PaymentProcessingError 예외 발생
            with pytest.raises(PaymentProcessingError):
                PaymentService.create_paypal_order(
                    amount=Decimal("750.00"),
                    currency="PHP",
                    description="Network Error Test"
                )
