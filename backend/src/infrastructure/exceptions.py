"""Infrastructure 계층 기술 예외"""


class InfrastructureException(Exception):
    """인프라 계층 기술 예외 기본 클래스"""
    pass


class PaymentProcessingError(InfrastructureException):
    """결제 처리 에러"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class EmailSendingError(InfrastructureException):
    """이메일 발송 에러"""
    pass


class AuthenticationError(InfrastructureException):
    """인증 기술 에러 (JWT 토큰 검증/생성 실패)"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class CacheError(InfrastructureException):
    """캐시 에러"""
    pass
