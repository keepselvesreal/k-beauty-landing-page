"""데이터베이스 연결 및 세션 관리"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ORM 베이스 클래스
Base = declarative_base()


def get_db():
    """데이터베이스 세션 의존성 주입"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
