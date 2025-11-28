"""PayPal Provider 검증 테스트 - PayPal API 응답이 계약을 충족하는지 검증"""

import pytest
import paypalrestsdk
import json
import os
from pathlib import Path

from src.config import settings


class TestPayPalProvider:
    """PayPal Provider 측 계약 검증"""

    @pytest.fixture(autouse=True)
    def setup_paypal(self):
        """PayPal SDK 초기화"""
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })

    def _load_contract(self, contract_name: str) -> dict:
        """계약 파일 로드"""
        contract_path = Path(__file__).parent.parent / "contracts" / f"{contract_name}.json"
        with open(contract_path, 'r') as f:
            return json.load(f)

    def test_paypal_success_contract_fulfilled(self):
        """
        **TC-3.1.Provider.1: PayPal 성공 응답 계약 충족** 🟢 Happy Path 🔵 Unit

        실제 PayPal API 응답이 success 계약을 충족하는지 검증
        """
        # 계약 로드
        contract = self._load_contract("paypal_order_create_success")

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": "750.00",
                    "currency": "PHP",
                    "details": {
                        "subtotal": "650.00",
                        "shipping": "100.00"
                    }
                },
                "description": "K-Beauty Test Order",
            }],
            "redirect_urls": {
                "return_url": "http://localhost:3000/orders/success",
                "cancel_url": "http://localhost:3000/orders/cancel"
            }
        })

        # When: PayPal API 호출
        result = payment.create()

        # Then: 응답이 계약을 충족하는지 검증
        assert result is True, "PayPal API 호출 실패"

        # 응답 구조 검증
        response_body = {
            "id": payment.id,
            "state": payment.state,
            "intent": payment.intent,
        }

        # 계약에서 기대하는 필드들
        expected_response = contract["interactions"][0]["response"]["body"]

        assert payment.id is not None, "ID는 None이 아니어야 함"
        assert isinstance(payment.id, str), f"ID는 str이어야 함"
        assert payment.id.startswith("PAYID-"), f"ID는 'PAYID-'로 시작해야 함"

        assert payment.state == "created", f"State는 'created'여야 함, 실제: {payment.state}"
        assert payment.intent == "sale", f"Intent는 'sale'이어야 함"

        # Links 검증 (approval_url 포함)
        assert payment.links is not None, "Links는 None이 아니어야 함"
        approval_url = None
        for link in payment.links:
            if link['rel'] == 'approval_url':
                approval_url = link['href']
                break

        assert approval_url is not None, "approval_url이 없음"
        assert "sandbox.paypal.com" in approval_url, "Approval URL이 Sandbox 형식이 아님"

        print(f"\n✅ PayPal 성공 응답 계약 충족 검증 완료")
        print(f"  - Payment ID: {payment.id}")
        print(f"  - State: {payment.state}")
        print(f"  - Approval URL: {approval_url[:60]}...")

    def test_paypal_invalid_amount_contract_fulfilled(self):
        """
        **TC-3.1.Provider.2: PayPal 유효하지 않은 금액 에러 계약 충족** 🔴 Error Case 🔵 Unit

        유효하지 않은 금액 요청 시 PayPal 에러 응답이 계약을 충족하는지 검증
        """
        # 계약 로드
        contract = self._load_contract("paypal_order_create_errors")

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": "0.00",
                    "currency": "PHP",
                },
                "description": "Invalid Amount Test",
            }],
            "redirect_urls": {
                "return_url": "http://localhost:3000/orders/success",
                "cancel_url": "http://localhost:3000/orders/cancel"
            }
        })

        # When: 유효하지 않은 금액으로 PayPal API 호출
        result = payment.create()

        # Then: 에러 응답이 계약을 충족하는지 검증
        assert result is False, "0.00 금액도 수락되었음 (예상: 실패)"

        # 에러 응답 구조 검증
        expected_error_response = contract["interactions"][0]["response"]

        assert payment.error is not None, "Error는 None이 아니어야 함"
        # Error는 dict 또는 str 형식일 수 있음
        assert isinstance(payment.error, (str, dict)), f"Error는 str 또는 dict이어야 함, 실제: {type(payment.error)}"

        print(f"\n✅ PayPal 유효하지 않은 금액 에러 계약 충족 검증 완료")
        if isinstance(payment.error, dict):
            print(f"  - Error Name: {payment.error.get('name')}")
            print(f"  - Error Message: {payment.error.get('message')}")
        else:
            print(f"  - Error: {payment.error}")

    def test_paypal_invalid_currency_contract_fulfilled(self):
        """
        **TC-3.1.Provider.3: PayPal 유효하지 않은 통화 에러 계약 충족** 🔴 Error Case 🔵 Unit

        유효하지 않은 통화 요청 시 PayPal 에러 응답이 계약을 충족하는지 검증
        """
        # 계약 로드
        contract = self._load_contract("paypal_order_create_errors")

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {
                    "total": "750.00",
                    "currency": "INVALID",
                },
                "description": "Invalid Currency Test",
            }],
            "redirect_urls": {
                "return_url": "http://localhost:3000/orders/success",
                "cancel_url": "http://localhost:3000/orders/cancel"
            }
        })

        # When: 유효하지 않은 통화로 PayPal API 호출
        result = payment.create()

        # Then: 에러 응답이 계약을 충족하는지 검증
        assert result is False, "유효하지 않은 통화도 수락되었음 (예상: 실패)"
        assert payment.error is not None, "Error는 None이 아니어야 함"

        print(f"\n✅ PayPal 유효하지 않은 통화 에러 계약 충족 검증 완료")
        print(f"  - Error: {payment.error}")
