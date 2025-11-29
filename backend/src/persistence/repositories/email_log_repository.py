"""이메일 로그 데이터 접근 계층"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import EmailLog


class EmailLogRepository:
    """Email Log Repository"""

    @staticmethod
    def create_email_log(
        db: Session,
        order_id: UUID,
        recipient_email: str,
        email_type: str,
        status: str,
        error_message: str | None = None,
    ) -> EmailLog:
        """이메일 로그 생성

        Args:
            db: 데이터베이스 세션
            order_id: 주문 ID
            recipient_email: 수신자 이메일
            email_type: 이메일 유형 (예: "order_confirmation")
            status: 발송 상태 ("sent" 또는 "failed")
            error_message: 오류 메시지 (발송 실패 시)

        Returns:
            생성된 EmailLog 객체
        """
        email_log = EmailLog(
            order_id=order_id,
            recipient_email=recipient_email,
            email_type=email_type,
            status=status,
            error_message=error_message,
            sent_at=datetime.utcnow() if status == "sent" else None,
        )
        db.add(email_log)
        db.commit()
        db.refresh(email_log)
        return email_log

    @staticmethod
    def get_email_logs_by_order(db: Session, order_id: UUID) -> list[EmailLog]:
        """주문의 모든 이메일 로그 조회

        Args:
            db: 데이터베이스 세션
            order_id: 주문 ID

        Returns:
            EmailLog 리스트
        """
        return db.query(EmailLog).filter(EmailLog.order_id == order_id).all()
