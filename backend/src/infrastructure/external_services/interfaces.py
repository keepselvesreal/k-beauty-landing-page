"""외부 서비스 인터페이스 (Protocol)"""

from typing import Protocol
from sqlalchemy.orm import Session

from src.persistence.models import Order


class IEmailService(Protocol):
    """이메일 서비스 인터페이스"""

    def send_order_confirmation(self, db: Session, order: Order) -> bool:
        ...

    def send_shipment_notification(self, db: Session, order: Order, carrier: str, tracking_number: str) -> bool:
        ...


class IPaymentService(Protocol):
    """결제 서비스 인터페이스"""

    def create_paypal_order(
        self,
        amount,
        currency: str,
        description: str,
        return_url: str = None,
        cancel_url: str = None,
    ) -> dict:
        ...
