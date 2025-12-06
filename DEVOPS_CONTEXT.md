# K-Beauty Landing Page - DevOps Context

DevOps 전문가 자문용 프로젝트 정보 문서

---

## 📋 프로젝트 개요

**프로젝트명**: K-Beauty Landing Page (Santa Here - 한국 미용 제품 판매)
**목적**: 온라인 주문 및 배송 관리 플랫폼
**팀 규모**: 개인 프로젝트 (1명)
**예상 사용자**: 필리핀 기반, 처음에는 소규모(월 1-10건 주문)

---

## 🏗️ 기술 스택

### **프론트엔드**
```
Framework: React 19.2.0 + TypeScript
Build Tool: Vite 6.2.0
Styling: Tailwind CSS (CDN)
Testing: Jest, Playwright (E2E)
Hosting Plan: Firebase Hosting (무료)
Key Libraries:
  - react-i18next: 다국어 지원
  - lucide-react: 아이콘
```

### **백엔드**
```
Framework: FastAPI 0.104.1
Language: Python 3.11
Database: PostgreSQL 15
Deployment Plan: Google Cloud Run (무료)
Database Plan: Google Cloud SQL (무료 크레딧)
Key Dependencies:
  - SQLAlchemy 2.0.23: ORM
  - Pydantic 2.5.0: 데이터 검증
  - PayPal SDK 1.13.1: 결제 처리
  - python-json-logger: 구조화된 로깅
```

### **DevOps/CI-CD**
```
Version Control: GitHub (Main branch)
CI/CD Platform: GitHub Actions (예정)
Container: Docker (미구현)
Container Registry: 미정 (Google Artifact Registry 검토 중)
Secret Management: Google Cloud Secret Manager (예정)
Monitoring: 미구현
Logging: 미구현
```

---

## 📁 프로젝트 구조

```
k-beauty-landing-page/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── OrderForm.tsx              # 👈 핵심: 주문 생성
│   │   │   ├── OrderConfirmation.tsx      # 👈 핵심: 주문 조회/확인
│   │   │   ├── AdminDashboard.tsx         # 부차: 관리자
│   │   │   ├── FulfillmentPartnerDashboard.tsx  # 부차: 배송담당자
│   │   │   ├── InfluencerDashboard.tsx   # 부차: 인플루언서
│   │   │   └── ... (기타)
│   │   ├── utils/api.ts                   # API 클라이언트
│   │   └── App.tsx                        # 라우팅
│   ├── package.json
│   ├── vite.config.ts
│   └── .env (로컬만, .gitignore 포함)
│
├── backend/
│   ├── src/
│   │   ├── main.py                        # FastAPI 앱 진입점
│   │   ├── config.py                      # 환경 설정
│   │   ├── presentation/http/routers/
│   │   │   ├── orders.py                  # 👈 주문 관련 API
│   │   │   ├── customers.py               # 👈 고객 관련 API
│   │   │   ├── auth.py
│   │   │   ├── fulfillment_partner.py
│   │   │   ├── influencer.py
│   │   │   └── inquiry.py
│   │   ├── persistence/                   # 데이터베이스
│   │   │   ├── database.py                # DB 연결
│   │   │   └── repositories/
│   │   └── workflow/services/             # 비즈니스 로직
│   ├── alembic/                           # 마이그레이션
│   ├── pyproject.toml
│   └── .env (로컬만, .gitignore 포함)
│
├── DATABASE_SCHEMA.md
├── ENV_MANAGEMENT.md
├── .env.example                           # 환경변수 템플릿
└── .gitignore
```

---

## 🌐 API 플로우 (핵심 기능)

### **주문 생성 흐름 (OrderForm.tsx)**
```
1. 사용자 입력 (이름, 이메일, 주소, 수량)
   ↓
2. POST /api/customers (고객 생성 또는 기존 고객 반환)
   Backend: customers.py:create_customer()
   ↓
3. POST /api/orders (주문 생성)
   Backend: orders.py:create_order()
   - 재고 확인
   - 주문번호 자동생성
   - 배송료 계산
   ↓
4. PayPal 결제 (프론트엔드 클라이언트 사이드)
   ↓
5. 결제 성공 → localStorage에 customer_email 저장
   → /order-confirmation/{ORDER_NUMBER} 리다이렉트
```

### **주문 확인 흐름 (OrderConfirmation.tsx)**
```
1. URL에서 주문번호 추출 (/order-confirmation/ORD-xxx)
   ↓
2. localStorage에서 이메일 읽기 (또는 사용자 입력)
   ↓
3. GET /api/orders/{order_number}?email={email}
   Backend: orders.py:get_order()
   - 이메일 검증 (보안)
   - 주문 정보 반환
   ↓
4. 페이지 표시
   - 주문번호, 상품, 수량, 배송지, 예상 배송날짜
```

---

## 📊 현재 DevOps 상태

### **✅ 있는 것**
- GitHub 저장소 (Public/Private: ?)
- .env 파일 분리 (.gitignore 설정)
- 환경 설정 구조 (config.py: dev/staging/prod)
- API 에러 핸들링 (기본 수준)
- 기본 테스트 설정 (Jest, Playwright)

### **❌ 없는 것**
- Docker 컨테이너화 (`Dockerfile` 미구현)
- CI/CD 파이프라인 (GitHub Actions 미구현)
- 모니터링/로깅 도구
- 헬스 체크 엔드포인트 (기본 `/health` 만 있음)
- 구조화된 로깅 (JSON 포맷 미적용)
- 자동 백업/복구 계획
- 성능 테스트/부하 테스트
- 보안 감사 (OWASP)

---

## 🎯 계획하는 인프라 (Google Cloud)

### **무료 크레딧 범위 내**

```
┌─────────────────────────────────────────────┐
│     Firebase Hosting (프론트엔드)            │
│  - Vite 빌드 산출물 배포                    │
│  - 무료: 월 10GB 스토리지, 360MB/일 대역폭  │
└────────────────────┬────────────────────────┘
                     │ (HTTPS + API 라우팅)
                     ↓
┌─────────────────────────────────────────────┐
│        Google Cloud Run (백엔드)             │
│  - FastAPI 애플리케이션 컨테이너            │
│  - 무료: 월 200만 요청, 36MB-GB 초 메모리  │
│  - 자동 스케일링, Cold Start ~3초            │
└────────────────────┬────────────────────────┘
                     │ (JDBC/HTTPS)
                     ↓
┌─────────────────────────────────────────────┐
│      Google Cloud SQL (데이터베이스)         │
│  - PostgreSQL 15                            │
│  - 무료: db-f1-micro (0.6GB RAM, 3GB SSD)  │
│  - Cloud SQL Proxy 연결                     │
└─────────────────────────────────────────────┘

(선택) Artifact Registry: Docker 이미지 저장소
(선택) Secret Manager: API 키, 결제 자격증명
(선택) Cloud Monitoring: 메트릭 수집
(선택) Cloud Logging: 중앙화된 로깅
```

---

## 🚀 DevOps 우선순위 (제시된 로드맵)

### **우선순위 1️⃣ (이 주 안에)**
- [ ] Docker 이미지 빌드 설정 (`backend/Dockerfile`)
- [ ] 환경변수 구조 재정비 (dev/staging/prod 분리)
- [ ] GitHub Actions 기본 워크플로우 작성
- [ ] 로컬에서 Docker 빌드/실행 테스트

**목표**: 배포 파이프라인 기초 구축

### **우선순위 2️⃣ (1-2주 내)**
- [ ] Cloud SQL 인스턴스 생성 및 연결
- [ ] Cloud Run 서비스 생성 (수동 배포 테스트)
- [ ] Firebase Hosting 설정
- [ ] GitHub Actions에서 자동 배포 연결
- [ ] CORS 설정 및 테스트

**목표**: 자동 배포 파이프라인 작동

### **우선순위 3️⃣ (2-4주 이후)**
- [ ] 헬스 체크 엔드포인트 개선 (DB 연결 확인)
- [ ] 구조화된 로깅 (Cloud Logging 통합)
- [ ] 에러 핸들링 및 재시도 로직 강화
- [ ] 기본 모니터링 설정 (Cloud Monitoring)
- [ ] 자동 백업 정책 수립

**목표**: 운영 안정성 확보

### **미결정 사항**
- [ ] Terraform 도입 여부 (3개월 후 재검토)
- [ ] 로그/메트릭 저장소 선택 (Cloud Logging vs 외부 도구)
- [ ] 보안 감사 계획 (언제부터 OWASP 체크)

---

## 💰 비용 고려사항 (무료 크레딧 범위)

### **월 할당량 (무료)**

| 서비스 | 무료 할당량 | 초과 시 비용 | 현황 |
|--------|-----------|-----------|-----|
| **Cloud Run** | 200만 요청 | $0.00002/요청 | 처음엔 안전 |
| **Cloud SQL (db-f1-micro)** | 포함됨 | ~$7/월 | 무료 크레딧으로 커버 |
| **Firebase Hosting** | 10GB 스토리지 | $0.18/GB | 안전 |
| **Cloud Logging** | 일부 포함 | $0.50/GB (초과) | 로그 크기 관리 필요 |
| **Outbound Network** | 1GB/월 | $0.12/GB | API 호출 최소화 |

### **비용 절감 전략**
- Cloud Run Cold Start 활용 (자주 쓰이지 않으면 자동 종료)
- 프론트엔드 이미지 최적화 (Hosting 대역폭 절감)
- 로그 레벨 제어 (DEBUG 로그 프로덕션에서 비활성화)

---

## 🔑 핵심 기술 결정 사항

### **현재 결정됨**
- ✅ 환경: Google Cloud (무료 크레딧)
- ✅ 프론트엔드 호스팅: Firebase Hosting
- ✅ 백엔드 호스팅: Cloud Run
- ✅ 데이터베이스: Cloud SQL (PostgreSQL)
- ✅ CI/CD: GitHub Actions
- ✅ 우선순위: 주문 생성 → 주문 확인 → 부가 기능

### **미결정**
- ❓ Terraform 도입 (추천: 3개월 후)
- ❓ Docker Registry (Google Artifact Registry vs Docker Hub)
- ❓ 모니터링 도구 (Cloud Monitoring vs Datadog vs NewRelic)
- ❓ 로깅 백엔드 (Cloud Logging vs ELK vs Splunk)
- ❓ 자동 스케일링 정책 (언제부터 동시성 관리)
- ❓ 보안 테스트 타이밍 (개발 중 vs 배포 전)
- ❓ 성능 벤치마크 목표 (주문 생성 응답시간 SLA)

---

## 🚨 알려진 문제/위험 요소

### **기술적 위험**
1. **Cold Start 지연**: Cloud Run 첫 요청 ~3초 → 사용자 경험 저하 가능
   - 완화: 프론트엔드에서 재시도 로직 추가 필요

2. **주문 데이터 일관성**: 결제 완료 후 주문 조회 실패 시나리오
   - 원인: 네트워크 지연, DB 연결 실패
   - 완화: 트랜잭션 관리, 멱등성 보장 필요

3. **환경변수 노출 위험**: `.env` 파일이 실수로 커밋될 수 있음
   - 완화: Secret Manager 도입 (우선순위 2에서)

4. **데이터베이스 커넥션 풀 부족**: 동시 요청 증가 시 연결 고갈
   - 완화: 커넥션 풀 설정, 타임아웃 조정 필요

### **운영 위험**
1. **모니터링 부재**: 배포 후 서비스 상태 파악 불가
   - 완화: Cloud Monitoring 기본 설정 (우선순위 3)

2. **로깅 부재**: 문제 발생 시 원인 파악 어려움
   - 완화: 구조화된 로깅 도입 (우선순위 3)

3. **자동 백업 미설정**: DB 손실 시 복구 불가능
   - 완화: Cloud SQL 자동 백업 활성화 필수

---

## ❓ 전문가에게 묻고 싶은 질문

1. **우선순위가 타당한가?**
   - 주문 폼/확인에 집중하는 게 맞나?
   - 초기 단계에서 빼야 할 것이 있나?

2. **테라폼 도입 시점**
   - 3개월 뒤가 적절한가?
   - 아니면 병행하는 게 낫나?

3. **성능 최적화**
   - Cloud Run Cold Start를 줄일 수 있는 방법?
   - Cloud SQL 커넥션 풀 권장 설정?

4. **보안**
   - 이 규모에서 필수적인 보안 조치는?
   - OWASP Top 10 중 우선순위는?

5. **비용 관리**
   - 무료 크레딧 소진 후 월 예상 비용?
   - 비용 최적화 팁?

6. **모니터링/로깅**
   - 처음부터 도입할 べき (must-have)?
   - 또는 문제가 생길 때 추가해도 되나?

7. **배포 전략**
   - 블루/그린 배포 필요한가?
   - 아니면 간단한 무중단 배포로 충분?

8. **테스트 전략**
   - 주문 흐름의 통합 테스트는 언제부터?
   - 프로덕션 배포 전 테스트 체크리스트?

---

## 📈 예상 성장 시나리오

### **초기 (1-3개월)**
- 월 10-50건 주문
- 동시 사용자: ~5명
- 무료 할당량 내에서 충분

### **성장 (3-6개월)**
- 월 100-500건 주문
- 동시 사용자: 20-50명
- Cloud Run 자동 스케일링 시작될 수 있음
- Staging 환경 필요성 증가 (Terraform 고려 시점)

### **안정화 (6-12개월)**
- 월 1000건 이상 주문
- 동시 사용자: 100+명
- 유료 인스턴스 고려 (Cloud SQL)
- 다중 리전 배포 검토

---

## 📞 추가 정보

**프로젝트 저장소**: GitHub (링크)
**현재 개발 환경**: Linux, Node.js 18+, Python 3.11
**Google Cloud 프로젝트 ID**: (설정 필요)
**관리자 연락처**: taesoo (태수)

---

**이 문서는 DevOps 전문가 자문을 받기 위한 컨텍스트 자료입니다.**
**마지막 업데이트**: 2025-12-04
