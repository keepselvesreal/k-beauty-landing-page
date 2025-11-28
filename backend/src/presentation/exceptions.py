"""HTTP 예외 정의"""

from fastapi import HTTPException, status


class OrderNotFoundException(HTTPException):
    """주문을 찾을 수 없음"""
    def __init__(self, order_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )


class InsufficientInventoryException(HTTPException):
    """재고 부족"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory: {message}"
        )


class InvalidPaymentException(HTTPException):
    """결제 오류"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment error: {message}"
        )
