# K-Beauty Landing Page 백엔드 레이어드 아키텍처 비판적 검토

**작성일**: 2025-12-05
**대상 서적**:
- Head First Software Architecture (6장)
- Fundamentals of Software Architecture (10장)

---

## 📋 Executive Summary

태수의 백엔드는 **현재 잘 구성된 기본적인 레이어드 아키텍처**를 가지고 있어. 하지만 책에서 제시한 기준으로 평가하면 **다음 영역에서 개선이 필요**해:

1. **Testability** 문제 - 높은 결합도, 의존성 주입 부재
2. **Responsiveness** 문제 - Sinkhole 안티패턴 위험
3. **계층 격리 명확화** - 개방/폐쇄 계층이 문서화되지 않음
4. **Services 계층 부재** - 공유 유틸리티가 흩어져 있음

---

## 🏗️ 현재 아키텍처 평가

### 1. 긍정적 평가 ✅

#### 1.1 명확한 계층 분리
```
현재 구조:
src/
├── presentation/        ← Presentation 계층
│   ├── http/routers/
│   ├── schemas/
│   └── exceptions.py
├── workflow/            ← Business 계층
│   ├── services/
│   ├── domain/
│   └── dtos/
├── persistence/         ← Persistence 계층
│   ├── repositories/
│   ├── models.py
│   └── database.py
└── utils/              ← 공유 유틸리티 (?)
    ├── auth.py
    └── exceptions.py
```

**장점**:
- 폴더 구조로 계층이 명확함
- 각 계층의 책임이 분리됨
- 패키지 네이밍 이해하기 쉬움

#### 1.2 좋은 에러 처리
```python
# orders.py
try:
    result = OrderService.create_order(...)
    return result["order"]
except OrderException as e:
    raise HTTPException(status_code=400, detail={...})
```

**장점**:
- Custom Exception 사용 (OrderException)
- Presentation에서 적절한 HTTP 에러 변환

#### 1.3 테스트 기초 구축
```
tests/
├── unit/
│   ├── workflow/services/
│   └── persistence/repositories/
└── integration/
```

**장점**:
- 단위 테스트 구조 이미 구성
- 의존성 주입 기반 테스트 fixture 사용 (conftest.py)

---

### 2. 비판적 평가 🔴

#### 2.1 **Testability 문제 - 높은 결합도**

**문제 코드 1: OrderService의 강한 결합**

```python
# workflow/services/order_service.py
class OrderService:
    @staticmethod
    def create_order(db: Session, customer_id: UUID, product_id: UUID, quantity: int, region: str) -> dict:
        # 1. 모든 Repository를 직접 호출
        customer = CustomerRepository.get_customer_by_id(db, customer_id)
        product = ProductRepository.get_product_by_id(db, product_id)
        is_available = InventoryRepository.check_inventory_available(db, product_id, quantity)
        shipping_rate = ShippingRepository.get_shipping_rate_by_region(db, region)

        # 2. 직접 모델 생성 및 조작
        order = OrderRepository.create_order(db, ...)
        order_item = OrderRepository.add_order_item(db, ...)

        # 3. 외부 서비스 호출
        payment_result = PaymentService.create_paypal_order(...)

        return {...}
```

**문제점**:
- 📌 **정적 메서드 사용**: 의존성 주입 불가능
  ```python
  # 이 코드는 테스트 불가능
  OrderService.create_order(db, ...)  # PaymentService도 항상 실제 호출됨
  ```

- 📌 **Persistence 계층과의 강한 결합**
  - Repository들을 `import` 해서 직접 호출
  - 테스트할 때 Repository들을 Mock할 수 없음

- 📌 **불필요한 모든 계층 통과 (Sinkhole)**
  - 간단한 고객 조회는 왜 비즈니스 로직을 모두 거쳐야 할까?
  - 모든 검증을 한 메서드에서 수행

**현재의 테스트 코드**:

```python
# tests/unit/workflow/services/test_order_service.py
def test_request_cancellation_success_before_shipping(
    self,
    test_db: Session,
    order_with_customer: Order,
):
    # 실제 DB를 사용해서 테스트 (진정한 단위 테스트가 아님)
    result = OrderService.request_cancellation(
        test_db,  # ← 실제 데이터베이스!
        order_number=order_with_customer.order_number,
        reason="Wrong size",
    )
    assert result["order"].cancellation_status == "cancel_requested"
```

**문제**:
- 테스트가 실제 데이터베이스에 의존
- 테스트 속도 느림 (DB I/O)
- 테스트 결과가 DB 상태에 의존

#### 2.2 **Responsiveness 문제 - Sinkhole 안티패턴**

**문제 코드: OrderService.create_order()**

```python
def create_order(db: Session, customer_id: UUID, product_id: UUID, quantity: int, region: str):
    # ❌ 모든 검증이 한 메서드에
    customer = CustomerRepository.get_customer_by_id(db, customer_id)         # 검증
    product = ProductRepository.get_product_by_id(db, product_id)             # 검증
    is_available = InventoryRepository.check_inventory_available(...)         # 검증
    shipping_rate = ShippingRepository.get_shipping_rate_by_region(db, region) # 검증

    # 간단한 주문 생성인데 너무 많은 계층 통과
    order = OrderRepository.create_order(db, ...)
    order_item = OrderRepository.add_order_item(db, ...)

    # 결제까지 시작? (이건 OrderService의 책임인가?)
    payment_result = PaymentService.create_paypal_order(...)
```

**흐름**:
```
Presentation (Router)
    ↓
OrderService (모든 검증 + 생성 + 결제)
    ├→ CustomerRepository (DB)
    ├→ ProductRepository (DB)
    ├→ InventoryRepository (DB)
    ├→ ShippingRepository (DB)
    ├→ OrderRepository (DB)
    └→ PaymentService (외부 API)

총 6-7개의 DB 쿼리 + API 호출!
```

**평가**: 이것이 책에서 말하는 **Architecture Sinkhole 안티패턴**
- 많은 계층을 거치지만 각 계층에서 실질적 처리 없음
- 결과: 불필요한 메모리, DB 커넥션, API 호출

#### 2.3 **계층 격리 문서화 부재**

**현재 상태**:
```python
# orders.py 라우터
@router.post("/{order_number}/cancel-request")
async def request_cancellation(order_number: str, request_data: CancellationRefundRequest, db: Session):
    # ??? 이 라우터가 어느 계층과 어떻게 상호작용하는지 불명확
    result = OrderService.request_cancellation(db, order_number, reason)
```

**문제**:
- 📌 각 계층이 **폐쇄**인지 **개방**인지 명시되지 않음
- 📌 라우터가 직접 Repository를 호출할 수 있는지 알 수 없음
- 📌 개발자들이 마음대로 계층 규칙을 위반할 수 있음

#### 2.4 **Services 계층 부재 - 공유 유틸리티 흩어짐**

**문제 코드**:

```python
# src/utils/auth.py (Presentation 계층?)
# src/utils/exceptions.py (어느 계층?)
# src/workflow/services/email_service.py (Business 계층?)
# src/workflow/services/payment_service.py (Business 계층?)

# 어디에 다음이 있을까?
# - 로깅
# - 감시(Auditing)
# - 데이트 유틸리티
```

**현재 구조의 문제**:
```
src/utils/
├── auth.py       ← 인증 (Presentation이 쓸 수 있나?)
└── exceptions.py ← 예외 (어느 계층이 쓸 수 있나?)

src/workflow/services/
├── email_service.py    ← Business? 아니면 Infrastructure?
├── payment_service.py  ← Business? 아니면 Infrastructure?
└── order_service.py
```

**개선 필요**:
- Email, Payment는 "비즈니스 로직"이 아니라 "외부 서비스 호출"
- Logging, Auditing을 명시적으로 관리할 **Services 계층**이 필요

---

## 📊 레이어드 아키텍처 특성 평가

현재 코드를 Head First & Fundamentals 책의 기준으로 평가:

| 특성 | 현재 평가 | 이유 |
|------|---------|------|
| **Simplicity** | ⭐⭐⭐⭐⭐ | 명확한 폴더 구조, 이해하기 쉬움 |
| **Testability** | ⭐⭐ | 정적 메서드, 의존성 주입 없음 |
| **Responsiveness** | ⭐⭐⭐ | Sinkhole 위험, 모든 쿼리 한 번에 실행 |
| **Deployability** | ⭐⭐⭐ | 작은 프로젝트이므로 OK, 커질수록 문제 |
| **Scalability** | ⭐⭐ | 모놀리식 특성, 기능 추가 시 OrderService 계속 비대해짐 |
| **Maintainability** | ⭐⭐⭐ | 지금은 OK, 의존성 주입 없어서 점점 어려워질 것 |

---

## 🎯 개선 방향

### 1. **의존성 주입(Dependency Injection) 도입** ⭐⭐⭐ 우선순위 최고

**현재 문제**:
```python
class OrderService:
    @staticmethod
    def create_order(db: Session, customer_id: UUID, ...):
        customer = CustomerRepository.get_customer_by_id(db, customer_id)
        # ❌ Repository를 직접 호출할 수 없음
```

**개선 방안**:
```python
# 1. Interface 정의
class ICustomerRepository(Protocol):
    def get_customer_by_id(self, db: Session, customer_id: UUID) -> Customer:
        ...

# 2. Service에 주입
class OrderService:
    def __init__(
        self,
        customer_repo: ICustomerRepository,
        product_repo: IProductRepository,
        inventory_repo: IInventoryRepository,
        shipping_repo: IShippingRepository,
        order_repo: IOrderRepository,
        payment_service: IPaymentService,
    ):
        self.customer_repo = customer_repo
        self.product_repo = product_repo
        # ...

    def create_order(
        self,
        customer_id: UUID,
        product_id: UUID,
        quantity: int,
        region: str,
    ) -> dict:
        customer = self.customer_repo.get_customer_by_id(customer_id)
        product = self.product_repo.get_product_by_id(product_id)
        # ...

# 3. 라우터에서 DI 컨테이너 사용
@router.post("")
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    order_service: OrderService = Depends(get_order_service),  # DI!
):
    result = order_service.create_order(...)
    return result["order"]
```

**테스트가 쉬워짐**:
```python
def test_create_order_with_mock():
    # Mock 주입
    mock_customer_repo = Mock(spec=ICustomerRepository)
    mock_product_repo = Mock(spec=IProductRepository)

    service = OrderService(
        customer_repo=mock_customer_repo,
        product_repo=mock_product_repo,
        # ...
    )

    # Mock 설정
    mock_customer_repo.get_customer_by_id.return_value = Customer(id=UUID(...))

    # 테스트 (실제 DB 없이!)
    result = service.create_order(...)

    # 검증
    mock_customer_repo.get_customer_by_id.assert_called_once()
```

---

### 2. **계층 격리 명확화 - 개방/폐쇄 선언** ⭐⭐⭐ 우선순위 높음

**개선 방안**:

```python
# src/presentation/http/routers/orders.py (Presentation 계층 - 폐쇄)
"""
이 모듈은 Presentation 계층입니다.
- 폐쇄 계층: 반드시 workflow.services를 거쳐야 합니다.
- 주의: persistence 계층에 직접 접근하면 안 됩니다.
"""

@router.post("")
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),  # ← workflow 계층만
):
    result = order_service.create_order(...)
    return result["order"]

# ❌ 이건 안 됨 (Presentation → Persistence 직접 접근)
# from src.persistence.repositories.order_repository import OrderRepository
# order = OrderRepository.get_order_by_id(db, order_id)

# src/workflow/services/order_service.py (Business 계층 - 폐쇄)
"""
이 모듈은 Business 계층입니다.
- 폐쇄 계층: 반드시 persistence 계층을 거쳐야 합니다.
- 주의: presentation 계층에 의존하면 안 됩니다.
"""

class OrderService:
    def __init__(
        self,
        customer_repo: ICustomerRepository,  # persistence 계층 (OK)
        # ...
    ):
        ...

# src/persistence/repositories/order_repository.py (Persistence 계층 - 폐쇄)
"""
이 모듈은 Persistence 계층입니다.
- 폐쇄 계층: 데이터베이스 접근만 담당합니다.
"""

class OrderRepository:
    @staticmethod
    def get_order_by_id(db: Session, order_id: UUID) -> Order:
        return db.query(Order).filter(Order.id == order_id).first()
```

**문서화 추가**:

```markdown
# Architecture Layer Governance

## 계층 구조

```
Presentation (폐쇄)
    ↓ 반드시 거쳐야 함
Business/Workflow (폐쇄)
    ↓ 반드시 거쳐야 함
Persistence (폐쇄)
    ↓
Database
```

## 접근 규칙

- ✅ Presentation은 workflow.services만 호출
- ✅ Business는 persistence.repositories만 호출
- ✅ 모든 계층은 services.shared_utils 사용 가능 (공유 유틸리티)
- ❌ Presentation이 Persistence 직접 호출 금지
- ❌ Business가 Presentation 호출 금지

## 거버넌스 도구

ArchUnit을 사용한 자동 검증 계획:

```python
layeredArchitecture()
    .layer("Presentation").definedBy("..presentation..")
    .layer("Business").definedBy("..workflow..")
    .layer("Persistence").definedBy("..persistence..")
    .whereLayer("Presentation").mayOnlyBeAccessedByLayers()
    .whereLayer("Business").mayOnlyBeAccessedByLayers("Presentation")
    .whereLayer("Persistence").mayOnlyBeAccessedByLayers("Business")
```
```

---

### 3. **Services 계층 신설 - 공유 유틸리티 격리** ⭐⭐ 우선순위 중간

**현재 문제**:

```
src/
├── utils/
│   ├── auth.py          ← 어디서 쓰나?
│   └── exceptions.py    ← 어디서 쓰나?
└── workflow/services/
    ├── email_service.py   ← 이게 Business인가?
    └── payment_service.py ← 이게 Business인가?
```

**개선 방안**:

```python
# src/services/ (새로운 Services 계층 - 개방)
"""
Services 계층: 모든 계층에서 사용 가능한 공유 유틸리티

개방 계층: 모든 계층에서 직접 접근 가능
- Presentation이 Logger 사용 가능
- Business가 EmailService 사용 가능
- Persistence가 필요 없음 (보통)
"""

# src/services/logger.py
class Logger:
    @staticmethod
    def info(message: str):
        print(f"[INFO] {message}")

# src/services/email_service.py (외부 서비스 호출 추상화)
class IEmailService(Protocol):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        ...

class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        # 실제 이메일 발송
        pass

# src/services/payment_service.py (외부 서비스 호출 추상화)
class IPaymentService(Protocol):
    def create_paypal_order(self, amount: Decimal, currency: str, ...) -> dict:
        ...

class PaymentService(IPaymentService):
    def create_paypal_order(self, amount: Decimal, currency: str, ...):
        # PayPal API 호출
        pass

# 새로운 구조
src/
├── presentation/
│   ├── http/routers/
│   ├── schemas/
│   └── exceptions.py
├── workflow/
│   ├── services/
│   │   └── order_service.py    (Business 로직만)
│   ├── domain/
│   └── dtos/
├── persistence/
│   ├── repositories/
│   ├── models.py
│   └── database.py
└── services/              ← 새로운 계층 (개방)
    ├── logger.py          ← Logger
    ├── email_service.py   ← 이메일 발송 (외부 서비스)
    ├── payment_service.py ← 결제 (외부 서비스)
    ├── auth_utils.py      ← 인증 유틸리티
    └── exceptions.py      ← Custom Exceptions
```

**사용 예시**:

```python
# workflow/services/order_service.py
from src.services.email_service import IEmailService
from src.services.logger import Logger

class OrderService:
    def __init__(
        self,
        customer_repo: ICustomerRepository,
        email_service: IEmailService,  # Services 계층 (개방)
    ):
        self.customer_repo = customer_repo
        self.email_service = email_service
        self.logger = Logger  # Services 계층 (개방)

    def create_order(self, ...):
        self.logger.info("Creating order...")
        # ...
        self.email_service.send_email(...)  # 외부 서비스 호출
```

**거버넌스 규칙에 추가**:

```
Services 계층 (개방 - 모든 계층에서 접근 가능)
```

---

### 4. **Sinkhole 안티패턴 해결** ⭐⭐ 우선순위 중간

**현재 문제**:

```python
# ❌ 이 메서드는 너무 많은 일을 함
def create_order(db, customer_id, product_id, quantity, region):
    # 1. 고객 조회
    # 2. 상품 조회
    # 3. 재고 확인
    # 4. 배송료 조회
    # 5. 주문 생성
    # 6. 주문 상품 추가
    # 7. 결제 시작
```

**개선 방안**:

```python
# ✅ 메서드를 분리하고 필요한 것만 호출
class OrderService:
    def __init__(self, customer_repo, order_repo, ...):
        self.customer_repo = customer_repo
        self.order_repo = order_repo
        # ...

    # 단순 조회: 검증 없이 바로 데이터 반환
    def get_order(self, order_id: UUID) -> Order:
        """Fast-Lane Reader: 단순 조회만"""
        return self.order_repo.get_order_by_id(order_id)

    # 복잡한 작업: 모든 검증 수행
    def create_order(self, customer_id: UUID, product_id: UUID, quantity: int, region: str) -> dict:
        """복잡한 비즈니스 로직이 필요한 경우만 호출"""
        # 검증들...
        return {"order": order, ...}

    # 상태 변경: 간단한 업데이트만
    def update_order_status(self, order_id: UUID, status: str) -> Order:
        """단순 상태 업데이트: Sinkhole 방지"""
        return self.order_repo.update_order_status(order_id, status)
```

**라우터에서 적절히 호출**:

```python
@router.get("/{order_number}")
async def get_order(order_number: str, order_service: OrderService = Depends(...)):
    # ✅ 단순 조회: Fast-Lane 사용
    return order_service.get_order(order_number)

@router.post("")
async def create_order(order_data: OrderCreate, order_service: OrderService = Depends(...)):
    # ✅ 복잡한 작업: 전체 로직 호출
    return order_service.create_order(...)
```

---

### 5. **캐싱 도입 - Responsiveness 개선** ⭐ 우선순위 낮음 (나중)

**개선 방안**:

```python
from functools import lru_cache

class ProductRepository:
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_product_by_id(product_id: UUID) -> Product:
        # 자주 조회하는 상품은 캐시됨
        return db.query(Product).filter(Product.id == product_id).first()
```

또는 Redis 사용:

```python
from redis import Redis

class OrderService:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def get_order(self, order_id: UUID) -> Order:
        # 캐시 확인
        cache_key = f"order:{order_id}"
        cached_order = self.redis_client.get(cache_key)
        if cached_order:
            return json.loads(cached_order)

        # 데이터베이스 조회
        order = self.order_repo.get_order_by_id(order_id)

        # 캐시에 저장 (5분)
        self.redis_client.setex(cache_key, 300, json.dumps(order))
        return order
```

---

## 📝 구현 로드맵

### Phase 1: 기초 (1주일) ⭐⭐⭐
1. **의존성 주입 프레임워크 도입**
   - FastAPI의 `Depends()` 활용 확대
   - 또는 `dependency-injector` 라이브러리

2. **OrderService 리팩토링**
   - 정적 메서드 → 인스턴스 메서드로 변경
   - Repository 주입 받기
   - 테스트 개선

3. **계층 격리 문서화**
   - ARCHITECTURE.md 작성
   - 각 파일에 계층 주석 추가

### Phase 2: 개선 (2-3주일) ⭐⭐
1. **Services 계층 신설**
   - `src/services/` 폴더 생성
   - Logger, Email, Payment 이동

2. **Sinkhole 해결**
   - OrderService 메서드 분리
   - Fast-Lane Reader 패턴 도입

3. **거버넌스 자동화**
   - ArchUnit 또는 Python 대체 도구 적용

### Phase 3: 최적화 (나중에) ⭐
1. **캐싱 도입**
   - Redis 또는 메모리 캐시
2. **비동기 처리**
   - EmailService, PaymentService 비동기화
3. **모니터링**
   - 응답 시간 추적

---

## 🎓 참고: 책의 핵심 개념 적용

### Head First Software Architecture 기준

| 개념 | 현재 상태 | 개선 후 |
|------|---------|--------|
| **기술적 분할** | ✅ 좋음 (Presentation/Business/Persistence) | ✅ 유지 |
| **계층의 책임** | ⚠️ 명확하지만 문서화 부재 | ✅ 문서화 추가 |
| **도메인 vs 계층** | ⚠️ 도메인이 계층을 통과 | ✅ 자연스러움 (DDD 아님) |
| **요청 흐름** | ⚠️ Sinkhole 위험 | ✅ 메서드 분리로 해결 |

### Fundamentals of Software Architecture 기준

| 개념 | 현재 상태 | 개선 후 |
|------|---------|--------|
| **계층 격리** | ❌ 부재 | ✅ 명확한 개방/폐쇄 선언 |
| **의존성 주입** | ❌ 정적 메서드만 사용 | ✅ DI 도입 |
| **거버넌스** | ❌ 자동화 없음 | ✅ ArchUnit 도입 계획 |
| **Testability** | ⚠️ DB 의존적 | ✅ Mock 기반 테스트 가능 |
| **Responsiveness** | ⚠️ 모든 쿼리 한 번에 | ✅ Fast-Lane Reader |

---

## ✨ 최종 평가

**현재 상태**: ⭐⭐⭐⭐ (4/5)
- 기초가 잘 다져져 있음
- 계층 구조가 명확함
- 이미 테스트 기반 구축

**개선 후 예상**: ⭐⭐⭐⭐⭐ (5/5)
- 테스트 용이성 대폭 향상
- 응답 속도 최적화
- 유지보수성 극대화
- 팀 온보딩 용이

**소요 시간**: 약 3-4주 (단계적 적용)

**추천**:
1️⃣ 의존성 주입부터 시작 (가장 큰 효과)
2️⃣ 계층 격리 문서화 (협력 개선)
3️⃣ Sinkhole 해결 (성능 개선)
4️⃣ Services 계층 신설 (장기 유지보수)

---

**문의사항이나 구현 시 더 자세한 코드 예시가 필요하면 언제든지 물어봐!** 🚀
