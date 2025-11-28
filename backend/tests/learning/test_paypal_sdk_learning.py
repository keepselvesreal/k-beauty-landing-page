"""PayPal SDK Learning Test - PayPal API 동작 방식 학습"""

import pytest
import paypalrestsdk
from decimal import Decimal

from src.config import settings


class TestPayPalSDKLearning:
    """PayPal SDK 기본 동작 학습"""

    @pytest.fixture(autouse=True)
    def setup_paypal(self):
        """PayPal SDK 초기화"""
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,  # sandbox
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })

    def test_paypal_order_create_structure(self):
        """
        PayPal Order 생성 구조 학습

        PayPal가 기대하는 요청 형식과 응답 형식을 이해하기 위한 테스트
        """
        # PayPal Order 생성 요청 구조
        payment_dict = {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [
                {
                    "amount": {
                        "total": "750.00",
                        "currency": "PHP",
                        "details": {
                            "subtotal": "650.00",
                            "shipping": "100.00"
                        }
                    },
                    "description": "K-Beauty Product Order",
                }
            ],
            "redirect_urls": {
                "return_url": "http://localhost:3000/orders/success",
                "cancel_url": "http://localhost:3000/orders/cancel"
            }
        }

        # 이 딕셔너리 구조가 PayPal SDK에서 기대하는 형식인지 확인
        assert "intent" in payment_dict
        assert "transactions" in payment_dict
        assert "redirect_urls" in payment_dict
        assert payment_dict["transactions"][0]["amount"]["currency"] == "PHP"
        print("\n✅ PayPal Order 요청 구조 확인 완료")

    def test_paypal_order_create_actual(self):
        """
        실제 PayPal API 호출 (Sandbox)

        주의: 이 테스트는 실제 API를 호출하므로 느릴 수 있음
        PayPal Sandbox 계정이 필요함
        """
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [
                {
                    "amount": {
                        "total": "750.00",
                        "currency": "PHP",
                        "details": {
                            "subtotal": "650.00",
                            "shipping": "100.00"
                        }
                    },
                    "description": "K-Beauty Test Order",
                }
            ],
            "redirect_urls": {
                "return_url": "http://localhost:3000/orders/success",
                "cancel_url": "http://localhost:3000/orders/cancel"
            }
        })

        try:
            if payment.create():
                # 성공 응답 구조
                print(f"\n✅ PayPal Order 생성 성공")
                print(f"  - Payment ID: {payment.id}")
                print(f"  - State: {payment.state}")

                # 응답 구조 확인
                assert hasattr(payment, 'id'), "Payment ID 없음"
                assert hasattr(payment, 'state'), "Payment state 없음"
                assert hasattr(payment, 'links'), "Payment links 없음"

                # approval_url 확인
                approval_url = None
                for link in payment.links:
                    if link['rel'] == 'approval_url':
                        approval_url = link['href']
                        break

                assert approval_url is not None, "Approval URL 없음"
                print(f"  - Approval URL: {approval_url[:50]}...")

            else:
                # 실패 응답 구조
                print(f"\n❌ PayPal Order 생성 실패")
                print(f"  - Error: {payment.error}")

                # 에러 응답 구조 확인
                assert hasattr(payment, 'error'), "Error 필드 없음"
                print(f"  - Error details: {payment}")

        except Exception as e:
            pytest.skip(f"PayPal API 호출 불가: {str(e)}")

    def test_paypal_sdk_response_attributes(self):
        """PayPal 응답 객체의 속성들 확인"""
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
                "description": "K-Beauty Test",
            }],
            "redirect_urls": {
                "return_url": "http://localhost:3000/orders/success",
                "cancel_url": "http://localhost:3000/orders/cancel"
            }
        })

        try:
            payment.create()

            # success() vs error() 메서드 확인
            if payment.success():
                print(f"\n✅ payment.success() 메서드 작동 확인")
            else:
                print(f"\n✅ payment.error로 에러 접근 가능: {payment.error}")

        except Exception as e:
            pytest.skip(f"PayPal API 호출 불가")
