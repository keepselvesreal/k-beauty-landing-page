"""Email Service 테스트"""

from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from src.persistence.models import Order
from src.infrastructure.external_services import EmailService


class TestSendOrderConfirmation:
    """주문 확인 이메일 발송"""

    def test_send_order_confirmation_success(
        self, test_db: Session, order_with_customer: Order
    ):
        """TC-4.1.1: 이메일 발송 성공"""
        # ===== GIVEN (준비 상태) =====
        test_db.add(order_with_customer)
        test_db.commit()

        # ===== WHEN (실행 동작) =====
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            # context manager 설정
            mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp.__exit__ = MagicMock(return_value=None)
            mock_smtp_class.return_value = mock_smtp

            result = EmailService.send_order_confirmation(test_db, order_with_customer)

        # ===== THEN (예상 결과) =====
        assert result is True
        # email_logs 확인
        assert len(order_with_customer.email_logs) > 0
        email_log = order_with_customer.email_logs[0]
        assert email_log.status == "sent"
        assert email_log.email_type == "order_confirmation"
        # SMTP 호출 확인
        mock_smtp.starttls.assert_called_once()
        mock_smtp.sendmail.assert_called_once()

    def test_send_order_confirmation_smtp_connection_failure(
        self, test_db: Session, order_with_customer: Order
    ):
        """TC-4.1.2: 이메일 발송 실패 - SMTP 연결 오류"""
        # ===== GIVEN (준비 상태) =====
        test_db.add(order_with_customer)
        test_db.commit()

        # ===== WHEN (실행 동작) =====
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = ConnectionError("SMTP connection timeout")

            result = EmailService.send_order_confirmation(test_db, order_with_customer)

        # ===== THEN (예상 결과) =====
        assert result is False
        # email_logs 확인
        assert len(order_with_customer.email_logs) > 0
        email_log = order_with_customer.email_logs[0]
        assert email_log.status == "failed"
        assert "connection" in email_log.error_message.lower()

    def test_send_order_confirmation_smtp_auth_failure(
        self, test_db: Session, order_with_customer: Order
    ):
        """TC-4.1.3: 이메일 발송 실패 - SMTP 인증 오류"""
        # ===== GIVEN (준비 상태) =====
        test_db.add(order_with_customer)
        test_db.commit()

        # ===== WHEN (실행 동작) =====
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            # context manager 설정
            mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp.__exit__ = MagicMock(return_value=None)
            # login 오류 설정
            mock_smtp.login.side_effect = Exception("Authentication failed")
            mock_smtp_class.return_value = mock_smtp

            result = EmailService.send_order_confirmation(test_db, order_with_customer)

        # ===== THEN (예상 결과) =====
        assert result is False
        # email_logs 확인
        assert len(order_with_customer.email_logs) > 0
        email_log = order_with_customer.email_logs[0]
        assert email_log.status == "failed"
        assert "authentication" in email_log.error_message.lower()
