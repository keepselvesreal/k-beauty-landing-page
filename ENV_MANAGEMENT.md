# 환경변수 관리 가이드

## 📍 구조

```
k-beauty-landing-page/
├── .env                 # ⭐ 중앙 환경변수 파일 (실제값, git 무시)
├── .env.example         # ⭐ 템플릿 (git 추적)
├── .gitignore           # ⭐ .env 제외 설정
│
├── backend/
│   └── .env → ../.env (심볼링크)
│
└── frontend/
    └── .env → ../.env (심볼링크)
```

## ✅ 장점

1. **단일 진실 공급원**
   - 모든 환경변수는 루트 `.env` 하나에만 존재
   - 수정 시 한 곳만 변경 → 백엔드/프런트 자동 동기화

2. **동기화 자동**
   - 심볼링크로 연결되어 있어 언제나 동일한 값 사용
   - 버전 관리 불일치 불가능

3. **보안**
   - git에 커밋되는 것은 `.env.example`만
   - `.env` 파일은 `.gitignore`로 자동 제외

4. **개발 편의성**
   - 로컬 개발: 루트 `.env` 수정 한 번으로 완료
   - 각 프로젝트가 별도 수정 불필요

## 📋 환경변수 분류

### 백엔드 전용 (FastAPI)
- `DATABASE_URL` (PostgreSQL 연결)
- `PAYPAL_CLIENT_SECRET` (백엔드에서만 사용)
- `SMTP_*` (이메일 설정)
- `PROFIT_PER_ORDER` (비즈니스 로직)

### 프런트엔드 전용 (Vite)
- `VITE_API_BASE_URL` (API 엔드포인트)
- `VITE_PAYPAL_CLIENT_ID` (클라이언트사이드)
- `VITE_APP_NAME` (앱 이름)

### 공유 (양쪽 모두 사용)
- `ENVIRONMENT` (development/staging/production)
- `PAYPAL_CLIENT_ID` (백엔드 전용이지만 `VITE_PAYPAL_CLIENT_ID`로 프런트에서 사용)

## 🚀 사용법

### 로컬 개발
```bash
# 루트 .env 수정 (모든 변수)
# backend/frontend 자동으로 해당 값들 읽음 (심볼링크)

# 백엔드 실행
cd backend
source .venv/bin/activate
python -m uvicorn src.main:app --reload

# 프런트 실행 (다른 터미널)
cd frontend
npm run dev
```

### 새 환경변수 추가 시
1. 루트 `.env` 에 추가
2. 루트 `.env.example` 에 템플릿 추가
3. 백엔드/프런트에서 해당 변수 사용
4. 끝! (심볼링크가 알아서 동기화)

## ⚠️ 주의사항

- `.env` 파일은 절대 git에 커밋하지 말 것
- 심볼링크가 깨졌다면: `rm .env && ln -s ../.env .env`
- 프로덕션 배포 시: GitHub Secrets 사용

## 📝 .gitignore

```
.env                # ❌ 커밋 금지
.env.*.local       # ❌ 커밋 금지
.env.example       # ✅ 커밋 필수
```

