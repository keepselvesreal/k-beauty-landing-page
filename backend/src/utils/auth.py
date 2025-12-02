"""JWT 토큰 관리 - Utils"""

from datetime import datetime, timedelta
import jwt

from ..config import settings
from .exceptions import AuthenticationError


class JWTTokenManager:
    """JWT 토큰 관리"""

    @classmethod
    def create_access_token(cls, payload: dict) -> str:
        """액세스 토큰 생성"""
        data = payload.copy()
        data["exp"] = datetime.utcnow() + timedelta(
            hours=settings.JWT_EXPIRATION_HOURS
        )

        token = jwt.encode(
            data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    @classmethod
    def verify_access_token(cls, token: str) -> dict:
        """액세스 토큰 검증"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError(
                code="TOKEN_EXPIRED",
                message="토큰이 만료되었습니다.",
            )
        except jwt.InvalidTokenError:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="유효하지 않은 토큰입니다.",
            )
