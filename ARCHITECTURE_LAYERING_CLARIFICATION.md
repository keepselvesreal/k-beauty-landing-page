# 레이어드 아키텍처 계층화 명확화 (Fundamentals 기반)

**기준**: Fundamentals of Software Architecture 10장

---

## 🎯 핵심 개념 정리

### **책의 정의**

```
"The layered architecture is a technically partitioned architecture
(as opposed to domain-partitioned architecture). This means, as you learned
in Chapter 9, that components are separated by their technical role in the
architecture (such as presentation or business) rather than by domain
(such as customer)."
```

**의미**:
- **기술적 분할** = Presentation, Business, Persistence, Database
- **도메인 분할** = Customer, Order, Payment (DDD 스타일)

---

## ❓ 질문 1: "도메인이 모든 계층에 분산돼 있지 않나? 그럼 왜 Workflow Service는 순수 Business만?"

### **책의 명확한 답**

```
"As a result, any particular business domain is spread throughout all
of the layers of the architecture. For example, the domain of "customer"
is contained in the Presentation layer, Business layer, Rules layer,
Services layer, and Database layer."
```

### **태수가 발견한 것이 정확해!** ✅

```
Order 도메인:
├─ Presentation
│  ├─ routers/orders.py     (HTTP 엔드포인트)
│  └─ schemas/orders.py     (Request/Response 스키마)
│
├─ Workflow/Business
│  ├─ services/order_service.py  (주문 비즈니스 로직)
│  └─ domain/models.py           (도메인 모델 정의)
│
├─ Persistence
│  ├─ repositories/order_repository.py  (DB 접근)
│  └─ models.py                         (ORM 모델)
│
└─ Database
   └─ orders 테이블
```

### **그럼 왜 "Workflow Service는 순수 Business만"이라고 한 건가?**

**답**: 오해를 바로잡을 시간이야!

```python
# workflow/services/ 에는 2가지가 섞여 있음:

❌ 현재 상황 (혼재)
├─ order_service.py              ✅ Business 로직
├─ affiliate_service.py          ✅ Business 로직
├─ email_service.py              ❌ Infrastructure (외부 서비스!)
├─ payment_service.py            ❌ Infrastructure (외부 서비스!)
└─ authentication_service.py      ❌ Infrastructure (인증 기술)

✅ 개선되어야 할 상태
workflow/services/
├─ order_service.py              ✅ Business 로직
├─ affiliate_service.py          ✅ Business 로직
└─ ...

infrastructure/external_services/
├─ email_service.py              ✅ Infrastructure
├─ payment_service.py            ✅ Infrastructure
└─ ...

infrastructure/auth/
├─ authentication_service.py      ✅ Infrastructure
└─ ...
```

### **Business Service vs Infrastructure Service의 구분**

**Business Service (순수 비즈니스 로직)**:
```python
# workflow/services/order_service.py
class OrderService:
    """주문 생성, 취소, 환불 등의 비즈니스 규칙"""

    def create_order(self, customer_id, product_id, quantity, region):
        # 비즈니스 로직: 재고 확인 → 가격 계산 → 주문 생성
        # 결과: Order 객체 (도메인 모델)
        return order

    def request_cancellation(self, order_number, reason):
        # 비즈니스 로직: 취소 가능한 상태 검증 → 상태 변경
        # 결과: 상태 변경된 Order
        return updated_order
```

**Infrastructure Service (외부 기술 통합)**:
```python
# infrastructure/external_services/payment_service.py
class PaymentService:
    """PayPal과의 통합 - 비즈니스 로직 아님, 기술 도구"""

    def create_paypal_order(self, amount, currency, description):
        # 기술: PayPal API 호출
        # 결과: PayPal Order ID (외부 시스템의 응답)
        return paypal_order_id

# infrastructure/external_services/email_service.py
class EmailService:
    """SMTP를 통한 이메일 발송 - 비즈니스 로직 아님, 기술 도구"""

    def send_order_confirmation(self, order):
        # 기술: SMTP 연결 및 이메일 발송
        # 결과: bool (발송 성공/실패)
        return success
```

### **핵심 구분**

| 특성 | Business Service | Infrastructure Service |
|------|------------------|------------------------|
| **목적** | 도메인 규칙 구현 | 외부 기술 호출 |
| **반환값** | 도메인 모델 (Order, Customer) | 기술 응답 (PayPal ID, bool) |
| **사용처** | Business 계층 중심 | 모든 계층에서 선택적 사용 |
| **변경 이유** | 비즈니스 규칙 변경 | 기술 공급자 변경 |
| **예시** | "주문 취소는 배송 전에만 가능" | "PayPal → Stripe로 변경" |

---

## ❓ 질문 2: "예외가 섞여 있는데 어떻게 분리해야 할까? Infrastructure로 이동할 예외는?"

### **현재 상황 분석**

```python
# src/utils/exceptions.py (혼재!)

class BusinessError(Exception):
    """비즈니스 로직 예외"""
    pass

# ✅ Business 예외들
class OrderException(BusinessError):
    """비즈니스: 주문 관련 규칙 위반"""
    pass

class InsufficientInventoryError(BusinessError):
    """비즈니스: 재고 부족 (도메인 규칙)"""
    pass

# ❌ Infrastructure 예외들 (여기에 있으면 안 됨!)
class PaymentProcessingError(BusinessError):
    """기술: PayPal API 호출 실패"""
    pass

class EmailSendingError(BusinessError):
    """기술: SMTP 연결 실패"""
    pass

class AuthenticationError(BusinessError):
    """기술: JWT 토큰 검증 실패"""
    pass
```

### **분리 기준 (책의 관점)**

**Business 예외** = "도메인 규칙 위반"

```python
# workflow/exceptions.py (또는 utils/exceptions.py에 유지)
class BusinessError(Exception):
    """비즈니스 로직 예외"""
    pass

class OrderException(BusinessError):
    """비즈니스: 주문 관련 규칙 위반"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

class InsufficientInventoryError(BusinessError):
    """비즈니스: 재고 부족"""
    pass

class StaleObjectStateError(BusinessError):
    """비즈니스: 낙관적 락 충돌"""
    pass

class EmailAuthenticationError(BusinessError):
    """비즈니스: 이메일 검증 실패 (도메인 규칙)"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
```

**Infrastructure 예외** = "기술 도구 사용 실패"

```python
# infrastructure/exceptions.py (새로 생성)
class InfrastructureException(Exception):
    """인프라 계층 기술 예외"""
    pass

class PaymentProcessingError(InfrastructureException):
    """기술: PayPal API 호출 실패"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

class EmailSendingError(InfrastructureException):
    """기술: SMTP 연결/발송 실패"""
    pass

class AuthenticationError(InfrastructureException):
    """기술: JWT 토큰 검증/생성 실패"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

class CacheError(InfrastructureException):
    """기술: Redis/Cache 오류"""
    pass
```

### **구분 방법 (5초 테스트)**

질문: "이 예외는 **도메인 규칙**을 위반했을 때 발생하는가?"

| 예외 | 질문 | 답 | 위치 |
|------|------|-----|------|
| `OrderException` | 주문 도메인 규칙 위반? | YES | **Business** |
| `InsufficientInventoryError` | 재고 도메인 규칙 위반? | YES | **Business** |
| `PaymentProcessingError` | PayPal API 호출 실패? (도메인 아님) | NO | **Infrastructure** |
| `EmailSendingError` | SMTP 발송 실패? (도메인 아님) | NO | **Infrastructure** |
| `AuthenticationError` | 토큰 검증 실패? (기술 도구) | NO | **Infrastructure** |

### **구체적인 분리 계획**

```bash
# 현재
src/
└── utils/
    └── exceptions.py (모두 섞여 있음)

# 개선 후
src/
├── workflow/
│   └── exceptions.py  (Business 예외만)
│       ├── OrderException
│       ├── InsufficientInventoryError
│       ├── EmailAuthenticationError (도메인: 이메일 인증 실패)
│       └── ...
│
└── infrastructure/
    └── exceptions.py  (Infrastructure 예외만)
        ├── PaymentProcessingError
        ├── EmailSendingError
        ├── AuthenticationError (기술: JWT 토큰 검증 실패)
        ├── CacheError
        └── ...
```

---

## ❓ 질문 3: "인증 파일이 왜 Infrastructure에 포함되나?"

### **책의 명확한 답 (Services Layer 개념)**

```
"For example, suppose your layered architecture's Business layer has
shared objects that contain common functionality for business components
(such as date and string utility classes, auditing classes, logging classes,
and so on)."
```

**핵심**: Services/Infrastructure 계층은 "공유 기술 기능"

### **현재 상황**

```python
# src/utils/auth.py
class JWTTokenManager:
    """JWT 토큰 생성/검증"""

    @classmethod
    def create_access_token(cls, payload: dict) -> str:
        # JWT 토큰 생성 (기술)
        ...

    @classmethod
    def verify_access_token(cls, token: str) -> dict:
        # JWT 토큰 검증 (기술)
        ...
```

**질문**: 이게 비즈니스 로직인가?

```
답: 아니다! 기술 기능이다.

왜?
- JWT는 "어떤 인증 기술을 사용할 것인가"의 기술적 선택
- 만약 OAuth로 바꾼다면? 함수명, 사용처는 같되 내부만 바뀜
- 도메인 로직이 아니라 "기술 구현"
```

### **책의 예시와 비교**

```
책의 예시:
- Date utilities (날짜 포맷팅 기술)
- Auditing classes (감시 기술)
- Logging classes (로깅 기술)

우리의 경우:
- JWT 토큰 관리 (인증 기술)
- Email 발송 (외부 서비스 기술)
- Payment 처리 (외부 서비스 기술)
- Cache (캐싱 기술)
```

### **"인증"이 Business vs Infrastructure인지 판단하기**

```python
# 질문 1: "사용자가 인증되었는가?"는 비즈니스인가?
# 답: 일부 YES (도메인 규칙: "주문은 인증된 사용자만 가능")

# 질문 2: "JWT 토큰을 어떻게 만드는가?"는 비즈니스인가?
# 답: NO (기술 선택: JWT vs OAuth vs Session)

# 결론:
# - 인증의 "필요성" = Business (비즈니스 규칙)
# - 인증의 "구현 방식" = Infrastructure (기술 도구)
```

### **올바른 계층화**

```python
# ✅ workflow/services/authentication_service.py (Business)
"""
비즈니스: 사용자 인증 규칙
"""
class AuthenticationService:
    def __init__(self, jwt_manager: JWTTokenManager):  # 주입!
        self.jwt_manager = jwt_manager

    def login(self, email: str, password: str) -> dict:
        # 비즈니스 로직: 사용자 확인, 비밀번호 검증
        user = self.user_repo.get_by_email(email)
        if not user:
            raise OrderException(code="USER_NOT_FOUND", message="...")

        if not self.password_hasher.verify(password, user.password_hash):
            raise OrderException(code="INVALID_PASSWORD", message="...")

        # 기술: JWT 토큰 생성 (Infrastructure 사용)
        token = self.jwt_manager.create_access_token({"user_id": user.id})
        return {"user": user, "token": token}

# ✅ infrastructure/auth/jwt_manager.py (Infrastructure)
"""
기술: JWT 토큰 생성/검증 (교체 가능한 기술)
"""
class JWTTokenManager:
    def create_access_token(self, payload: dict) -> str:
        # 기술 구현
        data = payload.copy()
        data["exp"] = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode(data, settings.JWT_SECRET_KEY, algorithm="HS256")
        return token

# ✅ infrastructure/auth/password_hasher.py (Infrastructure)
"""
기술: 비밀번호 해싱 (bcrypt 또는 다른 알고리즘 가능)
"""
class PasswordHasher:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
```

---

## 📊 3가지 예외 분류 정리

### **예외 분류 테이블**

| 예외명 | 의미 | 이유 | 위치 |
|--------|------|------|------|
| **OrderException** | 주문 규칙 위반 | 도메인 규칙 (배송 전만 취소 가능) | **Business** |
| **InsufficientInventoryError** | 재고 부족 | 도메인 규칙 (재고는 도메인 개념) | **Business** |
| **EmailAuthenticationError** | 이메일 검증 실패 | 도메인 규칙 (주문자 확인은 도메인) | **Business** |
| **PaymentProcessingError** | PayPal API 실패 | 기술 도구 (API 호출 실패) | **Infrastructure** |
| **EmailSendingError** | SMTP 발송 실패 | 기술 도구 (SMTP 연결 실패) | **Infrastructure** |
| **AuthenticationError** (JWT) | 토큰 검증 실패 | 기술 도구 (JWT는 구현 선택) | **Infrastructure** |

---

## 🔑 핵심 포인트 (책 기준)

### **1. 도메인은 분산된다 ✅**

```
Order 도메인은 Presentation, Business, Persistence, Database에 분산
But 각 계층에서는 다른 역할을 함:
- Presentation: Order 입력 UI
- Business: Order 비즈니스 규칙
- Persistence: Order 데이터 저장
- Database: Order 테이블
```

### **2. Business Service는 비즈니스 로직만 ✅**

```
workflow/services/ = 도메인 규칙 구현
infrastructure/ = 기술 도구 (교체 가능)

구분 기준: "이 변경은 비즈니스 규칙 때문인가?" YES = Business
```

### **3. 인증은 Infrastructure ✅**

```
왜?
- JWT는 구현 기술 (OAuth로 바꿀 수 있음)
- 도메인이 아니라 "기술 선택"
- 다른 기술 도구들(Logging, Caching)과 같은 위치

비유:
- "사용자는 인증되어야 한다" = Business
- "JWT 토큰을 사용하자" = Infrastructure
```

---

## ✅ 최종 정리

| 질문 | 책의 답 | 우리의 상황 | 개선 방향 |
|------|--------|-----------|---------|
| **도메인 분산?** | YES, 모든 계층에 분산 | ✅ 이미 그렇게 되어 있음 | 계속 유지 |
| **Business는 순수 비즈니스?** | YES, 기술 구현 아님 | ❌ email_service, payment_service 혼재 | 분리하기 |
| **예외 분리?** | Business vs 기술 | ❌ 모두 utils에 섞여 있음 | 분리하기 |
| **인증은 Infrastructure?** | YES, 기술 도구 | ❌ utils에 있음 | infrastructure/auth로 이동 |

---

**이제 명확하지?** 더 궁금한 부분이 있으면 물어봐! 🚀
