"""전역 pytest 설정 및 fixture"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.persistence.database import Base, get_db
from src.main import app


# 테스트용 데이터베이스 설정 (PostgreSQL)
@pytest.fixture(scope="session")
def test_db_engine():
    """테스트 데이터베이스 엔진 생성"""
    # 테스트 데이터베이스 URL
    test_database_url = "postgresql://test_user:test_pass@localhost:5432/ph_kbeauty_test"

    engine = create_engine(
        test_database_url,
        echo=False,
    )

    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    yield engine

    # 테스트 완료 후 모든 테이블 삭제
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """테스트 데이터베이스 세션"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(test_db):
    """FastAPI 테스트 클라이언트 (테스트 DB 의존성 주입)"""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()
