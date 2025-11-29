"""환경 설정 관리"""

from typing import Literal

from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    """공통 설정"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    SERVER_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/kbeauty"

    # PayPal
    PAYPAL_CLIENT_ID: str
    PAYPAL_CLIENT_SECRET: str
    PAYPAL_MODE: Literal["sandbox", "live"] = "sandbox"

    # Email (Google SMTP)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "K-Beauty Shop"

    # Business Settings
    PROFIT_PER_ORDER: int = 80
    AFFILIATE_COMMISSION_RATE: float = 0.2

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # VITE_ 변수들 무시


class DevelopmentSettings(Settings):
    """개발 환경 설정"""

    DEBUG: bool = True
    PAYPAL_MODE: Literal["sandbox", "live"] = "sandbox"


class ProductionSettings(Settings):
    """프로덕션 환경 설정"""

    DEBUG: bool = False
    PAYPAL_MODE: Literal["sandbox", "live"] = "live"


def get_settings() -> Settings:
    """환경에 따른 설정 로드"""
    environment = Settings().ENVIRONMENT

    if environment == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


settings = get_settings()
