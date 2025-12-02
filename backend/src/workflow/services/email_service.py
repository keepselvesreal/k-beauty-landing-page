"""이메일 비즈니스 로직 서비스"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.orm import Session

from src.config import settings
from src.persistence.models import Order
from src.persistence.repositories.email_log_repository import EmailLogRepository


class EmailService:
    """Email Service"""

    @staticmethod
    def send_order_confirmation(db: Session, order: Order) -> bool:
        """주문 확인 이메일 발송

        Args:
            db: 데이터베이스 세션
            order: 주문 객체

        Returns:
            발송 성공 여부 (True/False)
        """
        try:
            # 1. 이메일 내용 준비
            recipient_email = order.customer.email
            subject = f"주문 확인: {order.order_number}"

            # 간단한 이메일 본문
            body = f"""
            안녕하세요, {order.customer.name}님!

            주문이 확인되었습니다.

            주문번호: {order.order_number}
            주문금액: ₱{order.total_price}

            감사합니다!
            """

            # 2. SMTP 연결 및 이메일 발송
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                # 이메일 메시지 생성
                msg = MIMEMultipart()
                msg['From'] = settings.SMTP_FROM_EMAIL
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                # 발송
                server.sendmail(
                    settings.SMTP_FROM_EMAIL,
                    [recipient_email],
                    msg.as_string()
                )

            # 3. 성공 로그 기록
            EmailLogRepository.create_email_log(
                db,
                order_id=order.id,
                recipient_email=recipient_email,
                email_type="order_confirmation",
                status="sent",
            )

            return True

        except ConnectionError as e:
            # 연결 오류 로그 기록
            EmailLogRepository.create_email_log(
                db,
                order_id=order.id,
                recipient_email=order.customer.email,
                email_type="order_confirmation",
                status="failed",
                error_message=f"SMTP connection error: {str(e)}",
            )
            return False

        except Exception as e:
            # 기타 오류 로그 기록
            EmailLogRepository.create_email_log(
                db,
                order_id=order.id,
                recipient_email=order.customer.email,
                email_type="order_confirmation",
                status="failed",
                error_message=f"Email sending error: {str(e)}",
            )
            return False

    @staticmethod
    def send_shipment_notification(
        db: Session,
        order: Order,
        carrier: str,
        tracking_number: str,
    ) -> bool:
        """배송 시작 알림 이메일 발송

        Args:
            db: 데이터베이스 세션
            order: 주문 객체
            carrier: 택배사
            tracking_number: 운송장 번호

        Returns:
            발송 성공 여부 (True/False)
        """
        try:
            # 1. 이메일 내용 준비
            recipient_email = order.customer.email
            subject = f"배송 시작 알림: {order.order_number}"

            # 배송사별 배송 예상 시간 (필리핀 기준)
            delivery_estimate = {
                "LBC": "1-3 영업일",
                "2GO": "2-4 영업일",
                "Grab Express": "당일-1 영업일",
                "Lalamove": "당일 배송",
            }
            estimate = delivery_estimate.get(carrier, "2-3 영업일")

            body = f"""
            안녕하세요, {order.customer.name}님!

            주문하신 상품이 배송되었습니다.

            주문번호: {order.order_number}
            택배사: {carrier}
            운송장 번호: {tracking_number}
            배송 예상 시간: {estimate}

            감사합니다!
            """

            # 2. SMTP 연결 및 이메일 발송
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                # 이메일 메시지 생성
                msg = MIMEMultipart()
                msg['From'] = settings.SMTP_FROM_EMAIL
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                # 발송
                server.sendmail(
                    settings.SMTP_FROM_EMAIL,
                    [recipient_email],
                    msg.as_string()
                )

            # 3. 성공 로그 기록
            EmailLogRepository.create_email_log(
                db,
                order_id=order.id,
                recipient_email=recipient_email,
                email_type="shipment_notification",
                status="sent",
            )

            return True

        except ConnectionError as e:
            # 연결 오류 로그 기록
            EmailLogRepository.create_email_log(
                db,
                order_id=order.id,
                recipient_email=order.customer.email,
                email_type="shipment_notification",
                status="failed",
                error_message=f"SMTP connection error: {str(e)}",
            )
            return False

        except Exception as e:
            # 기타 오류 로그 기록
            EmailLogRepository.create_email_log(
                db,
                order_id=order.id,
                recipient_email=order.customer.email,
                email_type="shipment_notification",
                status="failed",
                error_message=f"Email sending error: {str(e)}",
            )
            return False

    @staticmethod
    def send_influencer_inquiry_email(
        affiliate_code: str,
        affiliate_email: str,
        message: str,
        admin_email: str,
    ) -> bool:
        """인플루언서 문의 이메일 발송

        Args:
            affiliate_code: 어필리에이트 코드
            affiliate_email: 인플루언서 이메일
            message: 문의 내용
            admin_email: 관리자 이메일

        Returns:
            발송 성공 여부 (True/False)
        """
        try:
            # 1. 이메일 내용 준비
            subject = f"[인플루언서 문의] {affiliate_code}"

            body = f"""
            인플루언서 문의가 들어왔습니다.

            어필리에이트 코드: {affiliate_code}
            인플루언서 이메일: {affiliate_email}

            문의 내용:
            {message}

            ---
            관리자 페이지에서 확인해주세요.
            """

            # 2. SMTP 연결 및 이메일 발송
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                # 이메일 메시지 생성
                msg = MIMEMultipart()
                msg['From'] = settings.SMTP_FROM_EMAIL
                msg['To'] = admin_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                # 발송
                server.sendmail(
                    settings.SMTP_FROM_EMAIL,
                    [admin_email],
                    msg.as_string()
                )

            return True

        except Exception as e:
            # 오류 발생
            return False
