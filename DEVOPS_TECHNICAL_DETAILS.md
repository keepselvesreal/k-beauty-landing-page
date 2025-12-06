# K-Beauty Landing Page - DevOps 기술 상세 정보

---

## 🔗 API 엔드포인트 맵핑

### **주문 생성 흐름 (OrderForm → 결제 → 주문 확인)**

#### **Step 1: 고객 생성 API**
```
Endpoint: POST /api/customers
Source: backend/src/presentation/http/routers/customers.py:create_customer()
Called from: frontend/src/components/OrderForm.tsx (주문폼 제출 시)

Request:
{
  "email": "customer@example.com",
  "name": "John Doe",
  "phone": "09123456789",
  "address": "Manila",
  "region": "NCR"
}

Response (Success):
{
  "id": "cust-uuid",
  "email": "customer@example.com",
  "name": "John Doe"
}

Error Scenarios:
- 400: 이메일 형식 오류
- 500: DB 연결 실패
- 시간초과: Cloud Run Cold Start 또는 DB 느림

Database Write: customers 테이블
```

#### **Step 2: 주문 생성 API**
```
Endpoint: POST /api/orders
Source: backend/src/presentation/http/routers/orders.py:create_order()
Called from: frontend/src/components/OrderForm.tsx

Request:
{
  "customer_id": "cust-uuid",
  "product_id": "product-1",
  "quantity": 1,
  "region": "NCR"
}

Processing:
1. 재고 확인 (inventory 테이블)
2. 배송료 계산 (region별 shipping_cost)
3. 주문 번호 자동 생성 (ORD-YYYYMMDD-XXXXX)
4. 상태: 'pending' 저장

Response (Success):
{
  "order_number": "ORD-20251204-00001",
  "customer_id": "cust-uuid",
  "total_amount": 850,  # 제품(500) + 배송료(350)
  "status": "pending"
}

Error Scenarios:
- 400: 재고 부족 (OrderException)
- 500: DB 트랜잭션 실패
- 타임아웃: DB 느림, 배송료 계산 오래 걸림

Database Write: orders, order_items 테이블
```

#### **Step 3: PayPal 결제 (프론트엔드)**
```
Location: frontend/src/components/OrderForm.tsx
PayPal SDK: 브라우저 클라이언트 사이드 처리

Flow:
1. OrderForm에서 PayPal 버튼 렌더링
2. 사용자 클릭 → PayPal 팝업
3. 결제 완료 → localStorage에 'customer_email' 저장
4. /order-confirmation/{ORDER_NUMBER} 리다이렉트

환경변수 필요:
- VITE_PAYPAL_CLIENT_ID (프론트)
```

#### **Step 4: 주문 조회 API**
```
Endpoint: GET /api/orders/{order_number}?email={email}
Source: backend/src/presentation/http/routers/orders.py:get_order()
Called from: frontend/src/components/OrderConfirmation.tsx

Request:
GET /api/orders/ORD-20251204-00001?email=customer@example.com

Processing:
1. order_number로 주문 조회
2. email 검증 (보안 - 본인의 주문만 볼 수 있도록)
3. customer, product, shipping 정보 조인

Response (Success):
{
  "order_number": "ORD-20251204-00001",
  "customer": {
    "email": "customer@example.com",
    "name": "John Doe",
    "address": "Manila, NCR"
  },
  "product": {
    "name": "K-Beauty Product",
    "quantity": 1
  },
  "order_status": "pending",
  "estimated_delivery": "2025-12-07",
  "total_amount": 850
}

Error Scenarios:
- 404: 주문 없음 (잘못된 ORDER_NUMBER)
- 401: 이메일 불일치 (보안 위반)
- 500: DB 연결 실패

Database Read: orders, customers, products 테이블
```

---

## 🔐 환경변수 매핑

### **백엔드 (backend/src/config.py)**

```python
# ENVIRONMENT
ENVIRONMENT: str = "development"  # → "production" in GCP
DEBUG: bool = True  # → False in production
LOG_LEVEL: str = "INFO"  # → "WARNING" in production

# API/SERVER
API_BASE_URL: str = "http://localhost:8000"  # → Cloud Run URL
FRONTEND_BASE_URL: str = "http://localhost:3000"  # → Firebase URL
SERVER_PORT: int = 8000  # → 8080 (Cloud Run requirement)

# DATABASE
DATABASE_URL: str = "postgresql://user:password@localhost:5432/kbeauty"
# → Cloud SQL Proxy: "postgresql://user:password@/kbeauty?host=/cloudsql/project:region:instance"

# PAYPAL
PAYPAL_CLIENT_ID: str  # ⚠️ Secret Manager 필수
PAYPAL_CLIENT_SECRET: str  # ⚠️ Secret Manager 필수
PAYPAL_MODE: str = "sandbox"  # → "live" in production

# EMAIL (Google SMTP)
SMTP_SERVER: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str  # ⚠️ Secret Manager 권장
SMTP_PASSWORD: str  # ⚠️ Secret Manager 필수
SMTP_FROM_EMAIL: str
SMTP_FROM_NAME: str = "K-Beauty Shop"

# JWT
JWT_SECRET_KEY: str = "your-secret-key-change-in-production"  # ⚠️ Secret Manager 필수
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_HOURS: int = 24

# BUSINESS
AFFILIATE_PAYMENT_DAYS: int = 30
ADMIN_EMAIL: str = "admin@example.com"
```

### **프론트엔드 (frontend/.env)**

```env
# Build-time variables
VITE_API_BASE_URL=http://localhost:8000
VITE_PAYPAL_CLIENT_ID=your_sandbox_client_id
VITE_APP_NAME=K-Beauty Shop

# Note:
# - VITE_ prefix로 시작하는 변수만 클라이언트에서 접근 가능
# - 민감한 정보(PayPal Secret)는 백엔드에서만 처리
# - 배포 시 GitHub Actions에서 VITE_API_BASE_URL을 Cloud Run URL로 대체
```

### **Google Cloud 배포 시 환경변수 주입 (예상)**

```bash
# Cloud Run 배포 명령어
gcloud run deploy k-beauty-backend \
  --image gcr.io/PROJECT_ID/k-beauty-backend:latest \
  --region asia-northeast1 \
  --set-env-vars "ENVIRONMENT=production,DEBUG=false,LOG_LEVEL=WARNING,PAYPAL_MODE=live" \
  --set-env-vars "API_BASE_URL=https://k-beauty-backend-XXXXX.run.app" \
  --set-env-vars "FRONTEND_BASE_URL=https://k-beauty-landing-page.firebaseapp.com" \
  --set-env-vars "SERVER_PORT=8080" \
  --set-env-vars "DATABASE_URL=postgresql://..." \
  --update-secrets "PAYPAL_CLIENT_ID=paypal-client-id:latest" \
  --update-secrets "PAYPAL_CLIENT_SECRET=paypal-client-secret:latest" \
  --update-secrets "JWT_SECRET_KEY=jwt-secret-key:latest" \
  --update-secrets "SMTP_PASSWORD=smtp-password:latest"
```

---

## 📊 데이터베이스 스키마 (관련 테이블)

### **customers 테이블**
```sql
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  address TEXT,
  region VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```
**DevOps 관점**:
- 인덱스: email (주문 조회 시 자주 검색)
- 크기: 소규모 (1000명 = ~100KB)

### **orders 테이블**
```sql
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  order_number VARCHAR(50) UNIQUE NOT NULL,  -- ORD-YYYYMMDD-XXXXX
  customer_id UUID FOREIGN KEY,
  product_id UUID FOREIGN KEY,
  quantity INT,
  total_amount DECIMAL(10, 2),
  shipping_cost DECIMAL(10, 2),
  status VARCHAR(20),  -- pending, paid, shipped, delivered, refunded
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```
**DevOps 관점**:
- 인덱스: order_number (주문 조회 쿼리의 주 조건)
- 인덱스: customer_id (고객별 주문 목록 조회)
- 크기 성장: 월 100건 주문 × 12개월 = 1200건 (관리 용이)

---

## 🌍 CORS 설정 (현재 상태)

### **현재 코드 (backend/src/main.py:23-29)**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.FRONTEND_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **현재 상태의 문제점**
```
개발: http://localhost:3000 ✅
스테이징: FRONTEND_BASE_URL (환경변수로 동적) ✅
프로덕션: Cloud Run과 Firebase 배포 URL 불일치 ❌

예:
- Cloud Run 백엔드: https://k-beauty-backend-abc123.run.app
- Firebase 프론트: https://k-beauty-landing-page.firebaseapp.com

→ CORS 에러 발생 가능
```

### **수정 필요 사항**
```python
# 배포 환경별로 동적으로 설정해야 함
ALLOWED_ORIGINS = settings.FRONTEND_BASE_URL.split(",")  # 쉼표로 구분

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],  # 필요한 메서드만
    allow_headers=["Content-Type", "Authorization"],  # 필요한 헤더만
    max_age=3600,  # 프리플라이트 캐시
)
```

---

## ⚠️ 현재 코드의 DevOps 이슈

### **1. API 타임아웃 없음**
```typescript
// frontend/src/components/OrderForm.tsx (문제)
const response = await fetch(`${API_BASE_URL}/api/customers`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(...)
  // ❌ 타임아웃 설정 없음
  // Cloud Run Cold Start(~3초) + DB 느림(~2초) = 5초 이상 대기
});

// 개선안
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000);

try {
  const response = await fetch(`${API_BASE_URL}/api/customers`, {
    signal: controller.signal,
    // ...
  });
} finally {
  clearTimeout(timeoutId);
}
```

### **2. 재시도 로직 없음**
```typescript
// frontend/src/components/OrderConfirmation.tsx (문제)
const response = await fetch(
  `${API_BASE_URL}/api/orders/${orderNumber}?email=${encodeURIComponent(emailToUse)}`
  // ❌ 실패하면 바로 에러 표시
  // Cloud Run 일시적 오류(cold start, DB timeout)에 취약
);

// 개선안: 지수 백오프 재시도
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('timeout')), 30000)
        )
      ]);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt - 1)));
    }
  }
}
```

### **3. 헬스 체크 불완전**
```python
# backend/src/main.py:42-45 (현재)
@app.get("/health")
async def health_check():
    return {"status": "ok"}  # ❌ 데이터베이스 연결 확인 안 함

# 개선안
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # DB 연결 확인
        db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": f"error: {str(e)}"}, 503

@app.get("/health/live")  # Liveness Probe (서버 살아있나)
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")  # Readiness Probe (트래픽 받을 준비됐나)
async def readiness(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return {"status": "not_ready"}, 503
```

### **4. 로깅이 기본 수준**
```python
# backend/src/presentation/http/routers/customers.py:21 (현재)
logger.info(f"고객 생성 요청: {customer_data.model_dump()}")
# ❌ 문자열 기반 로깅, 파싱 어려움

# 개선안 (구조화된 JSON 로깅)
logger.info(
    "customer_created",
    extra={
        "customer_id": customer.id,
        "email": customer.email,
        "region": customer.region,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request.headers.get("X-Request-ID")
    }
)
```

### **5. 에러 핸들링이 불일치**
```python
# backend/src/presentation/http/routers/orders.py:36-51 (부분)
except OrderException as e:
    raise HTTPException(
        status_code=400,
        detail={"code": e.code, "message": e.message}
    )
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail={"code": "INTERNAL_ERROR", "message": str(e)}  # ❌ 과도한 정보 노출
    )

# 개선안
except OrderException as e:
    raise HTTPException(
        status_code=400,
        detail={"code": e.code, "message": e.message}
    )
except Exception as e:
    logger.error(f"Internal error: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail={"code": "INTERNAL_ERROR", "message": "An error occurred"}
        # 클라이언트에는 최소한의 정보만 반환
    )
```

---

## 🐳 Docker 빌드 전략

### **권장 Dockerfile (멀티스테이지 빌드)**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 레이어 (변경 적을 때 캐시)
COPY backend/pyproject.toml backend/requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# 빌더에서 설치된 패키지만 복사 (이미지 크기 줄임)
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 애플리케이션 코드
COPY backend ./

# Cloud Run requirement
ENV PORT=8080
EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### **Docker 이미지 크기 예상**
```
python:3.11-slim base: ~120MB
+ FastAPI + dependencies: ~150MB
= 총 ~270MB

이미지 크기 최적화:
✅ slim 베이스 이미지 사용 (full 대비 절반)
✅ 멀티스테이지 빌드 (빌드 도구 제거)
✅ .dockerignore로 불필요 파일 제외
```

---

## 🔄 GitHub Actions 워크플로우 개요

### **예상 구조**
```yaml
name: Deploy to Google Cloud

on:
  push:
    branches: [main]

jobs:
  build-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # 1. 인증
      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      # 2. 이미지 빌드
      - run: |
          docker build -t gcr.io/$PROJECT_ID/k-beauty-backend:$GITHUB_SHA \
            -f backend/Dockerfile \
            .

      # 3. 레지스트리에 푸시
      - run: docker push gcr.io/$PROJECT_ID/k-beauty-backend:$GITHUB_SHA

      # 4. Cloud Run 배포
      - uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: k-beauty-backend
          region: asia-northeast1
          image: gcr.io/$PROJECT_ID/k-beauty-backend:$GITHUB_SHA
          env_vars: ENVIRONMENT=production
          secrets: |
            DATABASE_URL=db-password:latest
            JWT_SECRET_KEY=jwt-secret:latest

  build-frontend:
    runs-on: ubuntu-latest
    needs: build-backend  # 백엔드 먼저 배포
    steps:
      # 백엔드 URL 획득 후 프론트에 주입
      - env:
          VITE_API_BASE_URL: https://k-beauty-backend-${{ github.sha }}.run.app
        run: npm run build

      # Firebase 배포
      - uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_JSON }}
          projectId: ${{ secrets.GCP_PROJECT_ID }}
```

---

## 📈 모니터링 지표 (필요한 메트릭)

### **Cloud Run 메트릭**
- `run.googleapis.com/request_count`: 요청 수 (무료 할당량 추적)
- `run.googleapis.com/request_latencies`: 응답 시간 (Cold Start 감지)
- `run.googleapis.com/container_memory_utilization`: 메모리 사용률

### **Cloud SQL 메트릭**
- `cloudsql.googleapis.com/database/cpu/utilization`: CPU 사용률
- `cloudsql.googleapis.com/database/memory/utilization`: 메모리 사용률
- `cloudsql.googleapis.com/database/network/connections`: 활성 연결 수

### **애플리케이션 메트릭**
- 주문 생성 응답시간 (목표: < 500ms)
- 주문 조회 응답시간 (목표: < 200ms)
- 결제 API 성공률 (목표: > 99%)
- 데이터베이스 연결 실패율 (목표: 0%)

---

**이 문서는 DevOps 전문가와의 상담을 위한 기술 상세 자료입니다.**
