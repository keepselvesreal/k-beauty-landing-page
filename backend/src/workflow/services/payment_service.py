"""결제 비즈니스 로직 서비스"""

from decimal import Decimal

import paypalrestsdk

from src.config import settings
from src.utils.exceptions import PaymentProcessingError


class PaymentService:
    """Payment Service - PayPal 결제 처리"""

    @staticmethod
    def configure_paypal():
        """PayPal SDK 설정"""
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })

    @staticmethod
    def create_paypal_order(
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str = None,
        cancel_url: str = None,
    ) -> dict:
        """
        PayPal Order 생성

        Args:
            amount: 총액 (상품가 + 배송료)
            currency: 통화 코드 (PHP 등)
            description: 주문 설명
            return_url: 결제 완료 후 돌아올 URL
            cancel_url: 결제 취소 시 돌아올 URL

        Returns:
            {
                "success": bool,
                "paypal_order_id": str,
                "approval_url": str,
            }

        Raises:
            PaymentProcessingError: PayPal API 호출 실패 시
        """
        # PayPal SDK 설정
        PaymentService.configure_paypal()

        # 기본값 설정
        if return_url is None:
            return_url = f"{settings.FRONTEND_BASE_URL}/orders/success"
        if cancel_url is None:
            cancel_url = f"{settings.FRONTEND_BASE_URL}/orders/cancel"

        try:
            # PayPal Payment 생성
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [
                    {
                        "amount": {
                            "total": str(amount),
                            "currency": currency,
                        },
                        "description": description,
                    }
                ],
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                }
            })

            # PayPal API 호출
            if payment.create():
                # 성공: approval_url 추출
                approval_url = None
                for link in payment.links:
                    if link['rel'] == 'approval_url':
                        approval_url = link['href']
                        break

                if approval_url is None:
                    raise PaymentProcessingError(
                        code="NO_APPROVAL_URL",
                        message="PayPal에서 승인 URL을 반환하지 않음"
                    )

                return {
                    "success": True,
                    "paypal_order_id": payment.id,
                    "approval_url": approval_url,
                }
            else:
                # 실패: 에러 메시지 추출
                error_message = payment.error
                if isinstance(error_message, dict):
                    error_message = f"{error_message.get('name', 'UNKNOWN_ERROR')}: {error_message.get('message', 'Unknown error')}"

                raise PaymentProcessingError(
                    code="PAYPAL_ORDER_CREATION_FAILED",
                    message=f"PayPal Order 생성 실패: {error_message}"
                )

        except PaymentProcessingError:
            raise
        except ConnectionError as e:
            raise PaymentProcessingError(
                code="NETWORK_ERROR",
                message=f"PayPal API 연결 실패: {str(e)}"
            )
        except Exception as e:
            raise PaymentProcessingError(
                code="INTERNAL_ERROR",
                message=f"PayPal Order 생성 중 오류 발생: {str(e)}"
            )
