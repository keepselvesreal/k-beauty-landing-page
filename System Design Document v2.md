# K-Beauty Landing Page - System Design Document

---

## 📋 문서 정보

| 항목 | 내용 |
|------|------|
| **Version** | 2 |
| **Updated** | 2025-11-29 |
| **Note** | ⭐ Settings 테이블에 affiliate_commission_rate 추가 / ⭐ Affiliate, AffiliateErrorLog 테이블 추가 / ⭐ Order 모델에 affiliate_id 추가 |

---

## 1. 기술 스택

| 항목 | 선택 |
|------|------|
| 데이터베이스 | PostgreSQL |
| 백엔드 프레임워크 | FastAPI (Python) |
| 이메일 | Google SMTP |
| 결제 | PayPal (Sandbox → Live) |
| 아키텍처 | 레이어드 (Presentation → Workflow → Persistence) |
| 결제 로직 | TDD 필수 (PayPal 캡처) |

---

## 2. 환경변수 관리

### 관리 방식
- **로컬 개발**: `.env` 파일 (git 무시)
- **환경별 설정**: Python 클래스 기반 (development.py, production.py 등)
- **통합 템플릿**: `.env.example` (git 추적)
- **CI/CD**: GitHub Secrets → 환경변수 주입

### .gitignore 설정
```
.env                    # 로컬 개발용 (민감 정보)
.env.*.local           # 로컬 오버라이드
.env.production        # ❌ 절대 추가하지 말 것
```

---

## 3. 필수 환경변수

```bash
# DATABASE
DATABASE_URL=postgresql://user:password@localhost:5432/k_beauty_db

# PAYPAL
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
PAYPAL_MODE=sandbox  # sandbox or live

# EMAIL (Google SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com

# BUSINESS SETTINGS
PROFIT_PER_ORDER=80
⭐ AFFILIATE_COMMISSION_RATE=0.2

# FRONTEND & API
FRONTEND_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000

# SERVER
ENVIRONMENT=development  # development, staging, production
SERVER_PORT=8000
DEBUG=True
```

---

## 4. 지역별 배송료 관리

| 지역 | 배송료 |
|------|--------|
| NCR | 100 페소 |
| Luzon | 120 페소 |
| Visayas | 140 페소 |
| Mindanao | 160 페소 |

### 특징
- **관리**: DB 테이블 (shipping_rates)
- **수정**: 관리자 UI에서 변경 가능
- **적용**: 향후 생성되는 주문부터 자동 적용

---

## 5. DB 스키마 - 핵심 테이블

### customers
- 고객 정보 (email, name, phone, address)

### fulfillment_partners
- 필리핀 배송담당자
- **신규**: `last_allocated_at` (마지막 할당 시간)

### products
- 상품 정보 (name, description, price)

### partner_allocated_inventory
- 배송담당자별 할당 재고
- allocated_quantity: 분배한 총 수량
- remaining_quantity: 미배송 수량
- stock_version: 낙관적 락용

### orders
- 주문 정보
- 결제 상태: pending, paid, payment_failed, cancelled
- 배송 상태: pending, preparing, shipped, delivered
- fulfillment_partner_id: 담당 배송담당자
- ⭐ affiliate_id: 어필리에이트 ID (affiliate_code 대신 사용)
- profit: 주문 이윤 (고정값)
- affiliate_commission: 어필리에이트 수수료

### order_items
- 주문 상품 상세

### shipment_allocations
- 배송담당자별 주문 할당 기록

### shipments
- 배송 기록
- tracking_number, status, shipped_at

### email_logs
- 이메일 발송 로그
- status: sent, failed

### ⭐ affiliates (신규)
- 어필리에이트 정보
- code: UUID 기반 고유 코드
- name: 어필리에이트 이름
- email: 연락처 이메일
- is_active: 활성화 여부

### ⭐ affiliate_error_logs (신규)
- 어필리에이트 오류 기록
- order_id: 주문 ID
- affiliate_code: 입력받은 코드
- error_type: "INVALID_CODE" / "INACTIVE_AFFILIATE"
- error_message: 에러 메시지

### affiliate_sales
- 어필리에이트 판매 기록
- commission_amount: 이윤의 20%

### ⭐ settings (수정)
- 이윤, PayPal 수수료율, ⭐ 어필리에이트 수수료율 설정
- ⭐ affiliate_commission_rate: 어필리에이트 수수료율 (기본값: 0.2)

### shipping_rates
- 지역별 배송료
- region: NCR, Luzon, Visayas, Mindanao

---

## 6. 배송담당자 할당 전략

### 전략: 라운드 로빈 (Round Robin)

#### 할당 규칙
1. **1순위**: 가장 오래전에 할당받은 배송담당자 (`last_allocated_at` 기준)
2. **2순위**: 남은 재고가 많은 순

#### 할당 프로세스
1. 주문 발생 시 필요 수량 확인
2. 조건 만족하는 배송담당자 중 위 규칙으로 선택
3. 배송담당자의 재고 차감 (낙관적 락)
4. `last_allocated_at` 업데이트

#### 목적
- 배송담당자 간 공정한 일 분배
- 장기적 부하 균형 유지
- 일관성 있는 할당 (결정적)

---

## 7. 주요 비즈니스 로직

### 재고 관리
- 대량 구매 → `partner_allocated_inventory`에 사전 분배

### 주문 처리
- 라운드 로빈으로 배송담당자 자동 할당
- 재고 차감 (낙관적 락 사용)

### 배송 상태
- pending → paid → preparing → shipped

### 배송료 계산
- 고객 주소의 지역 기반 조회
- shipping_rates 테이블 참조

### ⭐ 어필리에이트
- ⭐ 주문 생성 시 affiliate_id (선택사항) 저장
- ⭐ 유효하지 않은 affiliate_code 또는 비활성화된 affiliate → affiliate_error_logs에 기록
- ⭐ 결제 완료 후 affiliate_id가 유효하면 commission 자동 계산 및 affiliate_sales 기록
- ⭐ Commission 계산: profit × affiliate_commission_rate (기본값: 80 × 0.2 = 16 PHP)
- 지급은 별도 처리

### 이메일
- ⭐ 결제 완료 후 배송담당자 할당 이전에 주문 확인 이메일 발송
- 발송 성공/실패 email_logs에 기록

---

## 8. 레이어드 아키텍처 구조

```
src/
├── main.py                          # FastAPI 진입점
├── config.py                        # 환경변수 설정 (development/production)
│
├── presentation/                    # HTTP 핸들링 계층
│   ├── exceptions.py               # HTTP 예외 (4xx, 5xx)
│   ├── http/routers/               # API 라우트
│   │   ├── orders.py              # /api/orders*
│   │   ├── customers.py           # /api/customers*
│   │   ├── shipping.py            # /api/shipping-rates*
│   │   ├── admin.py               # /api/admin/*
│   │   └── partners.py            # /api/partners/*
│   └── schemas/                    # Pydantic 스키마
│       ├── orders.py              # OrderCreate, OrderResponse
│       ├── customers.py           # CustomerCreate
│       ├── shipping.py            # ShippingRateResponse
│       └── errors.py              # 에러 응답
│
├── workflow/                        # 비즈니스 로직 계층
│   ├── order_workflow.py           # 주문 워크플로우 조율
│   ├── payment_workflow.py         # 결제 워크플로우 (TDD)
│   ├── shipping_workflow.py        # 배송 워크플로우
│   ├── services/                  # 비즈니스 로직 서비스
│   │   ├── order_service.py       # 주문 생성, 상태 관리
│   │   ├── payment_service.py     # PayPal 결제 (TDD)
│   │   ├── shipping_service.py    # 배송료 계산
│   │   ├── inventory_service.py   # 재고 차감
│   │   ├── ⭐ affiliate_service.py   # 어필리에이트 기록
│   │   ├── email_service.py       # 이메일 발송
│   │   └── fulfillment_service.py # 배송담당자 할당 (라운드 로빈)
│   └── dtos/                      # Data Transfer Objects
│       ├── order_dtos.py
│       ├── payment_dtos.py
│       ├── shipping_dtos.py
│       └── common_dtos.py
│
├── persistence/                     # 데이터 접근 계층
│   ├── database.py                 # DB 연결, 세션 관리
│   ├── models.py                   # SQLAlchemy ORM 모델
│   └── repositories/               # 데이터 접근 로직
│       ├── customer_repository.py
│       ├── order_repository.py
│       ├── product_repository.py
│       ├── shipping_repository.py
│       ├── fulfillment_partner_repository.py
│       ├── inventory_repository.py
│       ├── ⭐ affiliate_repository.py
│       └── email_log_repository.py
│
└── utils/                           # 유틸리티
    ├── logger.py                   # 로깅
    ├── exceptions.py               # 커스텀 예외
    ├── paypal_client.py            # PayPal API 클라이언트
    ├── email_sender.py             # Gmail SMTP 클라이언트
    └── validators.py               # 입력 검증
```

---

## 9. API 엔드포인트 (주요)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/orders` | 주문 생성 |
| POST | `/api/orders/{order_id}/capture` | PayPal 결제 캡처 (TDD 필수) |
| GET | `/api/orders/{order_number}` | 주문 조회 |
| POST | `/api/admin/allocate-inventory` | 배송담당자 재고 분배 |
| POST | `/api/partners/orders/{order_id}/ship` | 배송 발송 |
| GET | `/api/admin/shipping-rates` | 배송료 조회 |
| PUT | `/api/admin/shipping-rates/{region}` | 배송료 수정 |

---

## 10. 배송 비즈니스 플로우

```
1. 당신 (구매자)
   ↓
2. 한번에 대량 구매 (예: 상품 100개)
   ↓
3. 필리핀 보관소
   ↓
4. partner_allocated_inventory에 분배
   배송담당자 A (30개) | B (40개) | C (30개)
   ↓
5. 고객 주문 발생
   ↓
6. ⭐ 어필리에이트 코드 입력 (선택사항) → 유효성 검증 및 오류 기록
   ↓
7. 라운드 로빈으로 배송담당자 자동 할당
   (가장 오래전에 할당받은 배송담당자 우선)
   ↓
8. ⭐ 결제 완료 → 어필리에이트 commission 기록 (affiliate_id가 유효한 경우)
   ↓
9. ⭐ 주문 확인 이메일 발송
   ↓
10. 배송료 자동 계산 (지역 기반)
   ↓
11. 배송담당자가 택배 발송
   ↓
12. shipments 테이블 업데이트
   (status: shipped, tracking_number)
   ↓
13. last_allocated_at 업데이트
```

---

## 주의사항

- PayPal 결제 캡처는 TDD로 작성할 것
- 환경변수는 절대 git에 커밋하지 말 것
- 낙관적 락으로 재고 동시성 문제 해결
- 배송담당자 할당은 라운드 로빈으로 공정성 보장
- ⭐ 어필리에이트 commission은 결제 완료 후, 배송담당자 할당 전에 기록
- ⭐ 유효하지 않은 affiliate_code는 주문 생성을 방해하지 않음 (오류 기록만)
