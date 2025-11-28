"""커스텀 비즈니스 예외"""


class BusinessException(Exception):
    """비즈니스 로직 예외 기본 클래스"""
    pass


class InsufficientInventoryError(BusinessException):
    """재고 부족 에러"""
    pass


class StaleObjectStateError(BusinessException):
    """낙관적 락 충돌"""
    pass


class PaymentProcessingError(BusinessException):
    """결제 처리 에러"""
    pass


class EmailSendingError(BusinessException):
    """이메일 발송 에러"""
    pass


class OrderException(BusinessException):
    """주문 관련 에러"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)
