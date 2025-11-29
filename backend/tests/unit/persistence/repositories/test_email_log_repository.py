"""Email Log Repository 테스트"""

from sqlalchemy.orm import Session

import pytest

from src.persistence.models import EmailLog, Order
from src.persistence.repositories.email_log_repository import EmailLogRepository


class TestCreateEmailLog:
    """Email Log 생성"""

    def test_create_email_log_success(
        self, test_db: Session, order_with_customer: Order
    ):
        """TC-4.2.1: Email Log 생성 - 발송 성공"""
        # Given
        test_db.add(order_with_customer)
        test_db.commit()

        # When
        email_log = EmailLogRepository.create_email_log(
            test_db,
            order_id=order_with_customer.id,
            recipient_email="customer@example.com",
            email_type="order_confirmation",
            status="sent",
        )

        # Then
        assert email_log is not None
        assert email_log.order_id == order_with_customer.id
        assert email_log.recipient_email == "customer@example.com"
        assert email_log.email_type == "order_confirmation"
        assert email_log.status == "sent"
        assert email_log.sent_at is not None

    def test_create_email_log_failed(
        self, test_db: Session, order_with_customer: Order
    ):
        """TC-4.2.2: Email Log 생성 - 발송 실패"""
        # Given
        test_db.add(order_with_customer)
        test_db.commit()

        # When
        email_log = EmailLogRepository.create_email_log(
            test_db,
            order_id=order_with_customer.id,
            recipient_email="customer@example.com",
            email_type="order_confirmation",
            status="failed",
            error_message="SMTP connection timeout",
        )

        # Then
        assert email_log is not None
        assert email_log.status == "failed"
        assert email_log.error_message == "SMTP connection timeout"


class TestGetEmailLogsByOrder:
    """주문의 Email Log 조회"""

    def test_get_email_logs_by_order_success(
        self, test_db: Session, order_with_customer: Order
    ):
        """주문의 모든 Email Log 조회"""
        # Given
        test_db.add(order_with_customer)
        test_db.commit()

        # 2개의 이메일 로그 생성
        EmailLogRepository.create_email_log(
            test_db,
            order_id=order_with_customer.id,
            recipient_email="customer@example.com",
            email_type="order_confirmation",
            status="sent",
        )

        EmailLogRepository.create_email_log(
            test_db,
            order_id=order_with_customer.id,
            recipient_email="admin@example.com",
            email_type="order_notification",
            status="sent",
        )

        # When
        email_logs = EmailLogRepository.get_email_logs_by_order(
            test_db, order_with_customer.id
        )

        # Then
        assert len(email_logs) == 2
        assert email_logs[0].recipient_email == "customer@example.com"
        assert email_logs[1].recipient_email == "admin@example.com"

    def test_get_email_logs_by_order_empty(
        self, test_db: Session, order_with_customer: Order
    ):
        """이메일 로그가 없는 경우"""
        # Given
        test_db.add(order_with_customer)
        test_db.commit()

        # When
        email_logs = EmailLogRepository.get_email_logs_by_order(
            test_db, order_with_customer.id
        )

        # Then
        assert len(email_logs) == 0
