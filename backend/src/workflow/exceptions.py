"""Business 로직 예외"""


class BusinessError(Exception):
    """비즈니스 로직 예외 기본 클래스"""
    pass


class InsufficientInventoryError(BusinessError):
    """재고 부족 에러"""
    pass


class StaleObjectStateError(BusinessError):
    """낙관적 락 충돌"""
    pass


class OrderException(BusinessError):
    """주문 관련 에러"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class EmailAuthenticationError(BusinessError):
    """이메일 인증 실패 에러"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)
