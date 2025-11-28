"""FastAPI 애플리케이션 진입점"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
# from src.persistence.database import engine, Base

# 테이블 생성은 Alembic 마이그레이션으로 관리
# Base.metadata.create_all(bind=engine)

# FastAPI 앱 초기화
app = FastAPI(
    title="K-Beauty Landing Page API",
    description="K-Beauty 쇼핑몰 백엔드 API",
    version="0.1.0",
    debug=settings.DEBUG,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.FRONTEND_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "K-Beauty Landing Page API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
