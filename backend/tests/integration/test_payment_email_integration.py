"""결제 완료 후 이메일 발송 통합테스트"""

from unittest.mock import patch, MagicMock

import pytest

from src.workflow.services.email_service import EmailService
from src.workflow.services.affiliate_service import AffiliateService
from src.workflow.services.order_service import OrderService


class TestPaymentEmailIntegration:
    """결제 완료 후 이메일 발송 통합테스트"""

    def test_email_sent_after_payment_success(
        self, client, complete_test_data
    ):
        """TC-4.3.1 Integration: 결제 완료 → 이메일 발송"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: Order 생성 및 Affiliate 설정
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=2,
            region="NCR",
        )
        order = order_result["order"]

        affiliate_id = AffiliateService.validate_and_record_affiliate_on_order_creation(
            db,
            order,
            data["affiliate"].code,
        )
        order.affiliate_id = affiliate_id
        db.commit()

        # ===== WHEN (실행 동작) =====
        # Step 2: 결제 초기화
        with patch('src.workflow.services.payment_service.paypalrestsdk.Payment') as mock_payment_class:
            mock_payment = MagicMock()
            mock_payment.create.return_value = True
            mock_payment.id = "PAYID-EMAIL-TEST-001"
            mock_payment.state = "created"
            mock_payment.links = [
                {'rel': 'approval_url', 'href': 'https://www.sandbox.paypal.com/checkoutnow?token=EMAIL'},
            ]
            mock_payment_class.return_value = mock_payment

            OrderService.initiate_payment(db, order.id)

        # Step 3: 결제 완료
        order.status = "paid"
        db.commit()

        # Step 4: Affiliate Commission 기록
        AffiliateService.record_commission_if_applicable(db, order)

        # Step 5: 이메일 발송 (핵심 동작 - SMTP 모킹)
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value = mock_smtp

            email_sent = EmailService.send_order_confirmation(db, order)

        # ===== THEN (예상 결과) =====
        assert email_sent is True
        # email_logs 확인
        assert len(order.email_logs) > 0
        email_log = order.email_logs[0]
        assert email_log.status == "sent"
        assert email_log.email_type == "order_confirmation"
        assert email_log.recipient_email == data["customer"].email

    def test_order_proceeds_even_if_email_fails(
        self, client, complete_test_data
    ):
        """TC-4.3.2 Integration: 이메일 발송 실패해도 주문 진행"""
        data = complete_test_data
        db = data["db"]

        # ===== GIVEN (준비 상태) =====
        # Step 1: Order 생성
        order_result = OrderService.create_order(
            db,
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            quantity=1,
            region="NCR",
        )
        order = order_result["order"]

        # ===== WHEN (실행 동작) =====
        # Step 2: 결제 완료
        order.status = "paid"
        db.commit()

        # Step 3: 이메일 발송 실패 (SMTP 연결 오류)
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = ConnectionError("SMTP connection timeout")

            email_sent = EmailService.send_order_confirmation(db, order)

        # ===== THEN (예상 결과) =====
        # 이메일 발송 실패
        assert email_sent is False
        # email_logs에 실패 기록
        assert len(order.email_logs) > 0
        email_log = order.email_logs[0]
        assert email_log.status == "failed"
        # 주문은 정상 진행됨
        assert order.status == "paid"
