# Infrastructure 계층 분리 - 아키텍처 리팩토링 가이드

**작성일**: 2025-12-06
**목표**: `service` 계층 → `infrastructure` 계층으로 이름 변경 및 구조 개선

---

## 🎯 Infrastructure 계층이란?

### **이름이 `infrastructure`인 이유**

```
계층명 비교:

❌ "service" 계층
   - workflow.services와 헷갈림
   - "서비스"가 너무 광범위함
   - 비즈니스인지 기술인지 불명확

✅ "infrastructure" 계층
   - 외부 서비스 호출 추상화
   - 기술적 기능 담당 (non-business)
   - 계층의 역할이 명확함
```

### **Infrastructure 계층의 역할**

```python
"""
Infrastructure 계층: 외부 기술 기능을 추상화하는 계층

책에서의 정의:
- 모든 계층에서 접근 가능한 개방 계층
- Business 로직이 아님 (기술적 기능)
- 선택적 접근 가능 (필요할 때만)

포함 내용:
1. 외부 서비스 통합 (PayPal, Google SMTP, etc)
2. 기술 유틸리티 (로깅, 캐싱, 토큰 관리)
3. 기술적 예외 처리
4. 설정 관리
"""
```

---

## 📊 현재 vs 개선된 구조

### **현재 문제 상황**

```
src/
├── presentation/
│   ├── http/routers/
│   ├── schemas/
│   └── exceptions.py        ← 어느 계층?
│
├── workflow/
│   ├── services/            ← Business 서비스들...
│   │   ├── order_service.py
│   │   ├── affiliate_service.py
│   │   ├── email_service.py  ← ❌ 외부 서비스인데 여기?
│   │   └── payment_service.py ← ❌ 외부 서비스인데 여기?
│   ├── domain/
│   └── dtos/
│
├── persistence/
│   ├── repositories/
│   ├── models.py
│   └── database.py
│
└── utils/                    ← ❌ 어느 계층에 속하나?
    ├── auth.py              (JWT 토큰)
    └── exceptions.py        (기술적 예외)
```

**문제점**:
1. `workflow/services`에 Business와 Infrastructure 혼재
2. `utils`의 위치가 불명확
3. 개발자가 어디에 뭘 넣어야 할지 모호함

### **개선된 구조**

```
src/
├── presentation/               ← Presentation 계층 (폐쇄)
│   ├── http/
│   │   ├── routers/
│   │   ├── dependencies.py    (Depends() 정의)
│   │   └── middleware.py
│   ├── schemas/
│   └── exceptions.py          (HTTP 예외)
│
├── workflow/                   ← Business 계층 (폐쇄)
│   ├── services/              ★ 순수 비즈니스 로직만!
│   │   ├── order_service.py
│   │   ├── affiliate_service.py
│   │   ├── fulfillment_service.py
│   │   ├── shipment_service.py
│   │   ├── inquiry_service.py
│   │   ├── admin_service.py
│   │   └── authentication_service.py
│   ├── domain/
│   └── dtos/
│
├── persistence/                ← Persistence 계층 (폐쇄)
│   ├── repositories/
│   ├── models.py
│   └── database.py
│
├── infrastructure/             ← ★ Infrastructure 계층 (개방!)
│   ├── external_services/      (외부 서비스 호출)
│   │   ├── __init__.py
│   │   ├── email_service.py    (Google SMTP)
│   │   ├── payment_service.py  (PayPal)
│   │   └── interfaces.py       (추상 인터페이스)
│   │
│   ├── logger/                 (로깅)
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── config.py
│   │
│   ├── cache/                  (캐싱)
│   │   ├── __init__.py
│   │   ├── redis_cache.py
│   │   └── memory_cache.py
│   │
│   ├── auth/                   (인증/토큰)
│   │   ├── __init__.py
│   │   ├── jwt_manager.py
│   │   └── password_hasher.py
│   │
│   └── exceptions.py           (기술적 예외)
│
└── config.py                   ← 설정 (Infrastructure 관련)
```

---

## 📁 상세 구조 및 파일 이동

### **Phase 1: Infrastructure 폴더 생성**

```bash
# 새 폴더 생성
mkdir -p src/infrastructure/external_services
mkdir -p src/infrastructure/logger
mkdir -p src/infrastructure/cache
mkdir -p src/infrastructure/auth
```

### **Phase 2: 파일 이동 및 리팩토링**

#### **2.1 외부 서비스 - `external_services/`**

**원본**:
```
src/workflow/services/email_service.py      (140줄)
src/workflow/services/payment_service.py    (125줄)
```

**이동 후**:
```python
# src/infrastructure/external_services/__init__.py
from .email_service import EmailService
from .payment_service import PaymentService
from .interfaces import IEmailService, IPaymentService

__all__ = [
    "EmailService",
    "PaymentService",
    "IEmailService",
    "IPaymentService",
]

# src/infrastructure/external_services/interfaces.py
"""외부 서비스 인터페이스 (Protocol)"""

from typing import Protocol
from email.mime.multipart import MIMEMultipart

class IEmailService(Protocol):
    """이메일 서비스 인터페이스"""
    def send_order_confirmation(self, order) -> bool:
        ...

    def send_shipment_notification(self, order, carrier, tracking_number) -> bool:
        ...

class IPaymentService(Protocol):
    """결제 서비스 인터페이스"""
    def create_paypal_order(self, amount, currency, description, return_url=None, cancel_url=None) -> dict:
        ...

# src/infrastructure/external_services/email_service.py
"""이메일 발송 서비스 - Google SMTP"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from src.config import settings
from src.persistence.models import Order
from src.persistence.repositories.email_log_repository import EmailLogRepository
from .interfaces import IEmailService

class EmailService(IEmailService):
    """Google SMTP를 사용한 이메일 발송"""

    @staticmethod
    def send_order_confirmation(db: Session, order: Order) -> bool:
        """주문 확인 이메일 발송"""
        # 기존 코드와 동일
        ...

    @staticmethod
    def send_shipment_notification(db: Session, order: Order, carrier: str, tracking_number: str) -> bool:
        """배송 시작 알림 이메일 발송"""
        # 기존 코드와 동일
        ...

# src/infrastructure/external_services/payment_service.py
"""결제 처리 서비스 - PayPal"""

from decimal import Decimal
import paypalrestsdk
from src.config import settings
from src.infrastructure.exceptions import PaymentProcessingError
from .interfaces import IPaymentService

class PaymentService(IPaymentService):
    """PayPal을 사용한 결제 처리"""

    @staticmethod
    def configure_paypal():
        """PayPal SDK 설정"""
        # 기존 코드와 동일
        ...

    @staticmethod
    def create_paypal_order(
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str = None,
        cancel_url: str = None,
    ) -> dict:
        """PayPal Order 생성"""
        # 기존 코드와 동일
        ...
```

#### **2.2 로깅 - `logger/`**

```python
# src/infrastructure/logger/__init__.py
from .logger import Logger, get_logger

__all__ = ["Logger", "get_logger"]

# src/infrastructure/logger/logger.py
"""애플리케이션 로거"""

import logging
import sys
from datetime import datetime

class Logger:
    """애플리케이션 로거"""

    @staticmethod
    def get_logger(name: str):
        """로거 인스턴스 생성"""
        logger = logging.getLogger(name)

        if not logger.handlers:
            # 핸들러 설정
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

def get_logger(name: str):
    """편의 함수"""
    return Logger.get_logger(name)

# 사용 예시
logger = get_logger(__name__)
logger.info("Application started")
```

#### **2.3 캐싱 - `cache/`**

```python
# src/infrastructure/cache/__init__.py
from .redis_cache import RedisCache
from .memory_cache import MemoryCache

__all__ = ["RedisCache", "MemoryCache"]

# src/infrastructure/cache/redis_cache.py
"""Redis 캐시"""

import json
from typing import Any, Optional
import redis

class RedisCache:
    """Redis 기반 캐시"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장"""
        self.client.setex(key, ttl, json.dumps(value, default=str))

    def delete(self, key: str):
        """캐시에서 값 삭제"""
        self.client.delete(key)

    def clear(self):
        """전체 캐시 삭제"""
        self.client.flushdb()

# src/infrastructure/cache/memory_cache.py
"""메모리 기반 캐시 (개발 환경용)"""

from functools import lru_cache
from typing import Any, Optional
from datetime import datetime, timedelta

class MemoryCache:
    """메모리 기반 캐시 (간단한 캐싱용)"""

    def __init__(self):
        self.store = {}
        self.expiry = {}

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key in self.store:
            if key in self.expiry and self.expiry[key] < datetime.now():
                del self.store[key]
                del self.expiry[key]
                return None
            return self.store[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장"""
        self.store[key] = value
        self.expiry[key] = datetime.now() + timedelta(seconds=ttl)

    def delete(self, key: str):
        """캐시에서 값 삭제"""
        if key in self.store:
            del self.store[key]
            if key in self.expiry:
                del self.expiry[key]

    def clear(self):
        """전체 캐시 삭제"""
        self.store.clear()
        self.expiry.clear()
```

#### **2.4 인증/토큰 - `auth/`**

**원본**:
```
src/utils/auth.py (JWT 토큰 관리)
```

**이동 후**:
```python
# src/infrastructure/auth/__init__.py
from .jwt_manager import JWTTokenManager
from .password_hasher import PasswordHasher

__all__ = ["JWTTokenManager", "PasswordHasher"]

# src/infrastructure/auth/jwt_manager.py
"""JWT 토큰 관리"""

from datetime import datetime, timedelta
import jwt
from src.config import settings
from src.infrastructure.exceptions import AuthenticationError

class JWTTokenManager:
    """JWT 토큰 생성/검증"""

    @classmethod
    def create_access_token(cls, payload: dict) -> str:
        """액세스 토큰 생성"""
        data = payload.copy()
        data["exp"] = datetime.utcnow() + timedelta(
            hours=settings.JWT_EXPIRATION_HOURS
        )

        token = jwt.encode(
            data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    @classmethod
    def verify_access_token(cls, token: str) -> dict:
        """액세스 토큰 검증"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError(
                code="TOKEN_EXPIRED",
                message="토큰이 만료되었습니다.",
            )
        except jwt.InvalidTokenError:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="유효하지 않은 토큰입니다.",
            )

# src/infrastructure/auth/password_hasher.py
"""비밀번호 해싱 (향후 추가)"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHasher:
    """비밀번호 해싱"""

    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
```

#### **2.5 예외 처리 - `exceptions.py`**

**원본**:
```
src/utils/exceptions.py
src/presentation/exceptions.py
```

**통합 후**:
```python
# src/infrastructure/exceptions.py
"""Infrastructure 계층 예외"""

class InfrastructureException(Exception):
    """Infrastructure 계층 기본 예외"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")

class PaymentProcessingError(InfrastructureException):
    """결제 처리 오류"""
    pass

class EmailSendingError(InfrastructureException):
    """이메일 발송 오류"""
    pass

class AuthenticationError(InfrastructureException):
    """인증 오류"""
    pass

class CacheError(InfrastructureException):
    """캐시 오류"""
    pass
```

---

## 🔄 Import 경로 변경

### **변경 전**

```python
# workflow/services/order_service.py
from src.workflow.services.payment_service import PaymentService
from src.workflow.services.email_service import EmailService
from src.utils.auth import JWTTokenManager
from src.utils.exceptions import OrderException

# presentation/http/routers/orders.py
from src.utils.exceptions import OrderException
```

### **변경 후**

```python
# workflow/services/order_service.py
from src.infrastructure.external_services import PaymentService, EmailService
from src.infrastructure.auth import JWTTokenManager
from src.utils.exceptions import OrderException  # Business 예외는 여전히 utils

# presentation/http/routers/orders.py
from src.utils.exceptions import OrderException  # Business 예외

# infrastructure/exceptions.py (새로운 위치)
from src.infrastructure.exceptions import PaymentProcessingError, EmailSendingError
```

---

## 🏗️ 계층 의존성 다이어그램

### **이전 (혼란스러움)**

```
Presentation
    ↓
Business (workflow/services)
    ├→ order_service (Business)
    ├→ payment_service (Infrastructure? Business?)
    ├→ email_service (Infrastructure? Business?)
    └→ utils (어디 위치?)
```

### **이후 (명확함)**

```
Presentation (폐쇄)
    ├→ Infrastructure (Logger, Auth) ← 선택적 접근
    └→ Business (폐쇄)
        ├→ Infrastructure (external services) ← 선택적 접근
        └→ Persistence (폐쇄)
            ├→ Infrastructure (Logger, Cache) ← 선택적 접근
            └→ Database
```

**규칙**:
- Presentation ➜ Business (폐쇄)
- Business ➜ Persistence (폐쇄)
- 모든 계층 ➜ Infrastructure (개방, 선택적)

---

## 📝 마이그레이션 체크리스트

### **Step 1: 폴더 구조 생성**
- [ ] `src/infrastructure/` 생성
- [ ] `src/infrastructure/external_services/` 생성
- [ ] `src/infrastructure/logger/` 생성
- [ ] `src/infrastructure/cache/` 생성
- [ ] `src/infrastructure/auth/` 생성

### **Step 2: 파일 이동**
- [ ] `src/workflow/services/email_service.py` → `src/infrastructure/external_services/`
- [ ] `src/workflow/services/payment_service.py` → `src/infrastructure/external_services/`
- [ ] `src/utils/auth.py` → `src/infrastructure/auth/jwt_manager.py`
- [ ] 예외 파일 통합

### **Step 3: Import 업데이트**
- [ ] `workflow/services/*.py` import 변경
- [ ] `presentation/http/routers/*.py` import 변경
- [ ] 모든 테스트 파일 import 변경

### **Step 4: 테스트**
- [ ] 모든 단위 테스트 실행
- [ ] 모든 통합 테스트 실행
- [ ] 애플리케이션 시작 확인

### **Step 5: 문서화**
- [ ] Architecture 문서 업데이트
- [ ] README 업데이트
- [ ] 개발 가이드 작성

---

## 🎯 이 구조의 이점

### **1. 명확한 의도** ⭐⭐⭐
```
infrastructure/ = "외부 기술과의 통합"
workflow/services/ = "순수 비즈니스 로직"

개발자가 즉시 이해!
```

### **2. 계층 격리** ⭐⭐⭐
```
Business가 Infrastructure 호출 가능
Infrastructure가 Business 호출 불가 (좋은 설계)
```

### **3. 테스트 용이성** ⭐⭐⭐
```python
# Mock 주입이 명확함
service = OrderService(
    payment_service=MockPaymentService(),  # Infrastructure Mock
    email_service=MockEmailService(),      # Infrastructure Mock
)
```

### **4. 확장성** ⭐⭐⭐
```
새로운 외부 서비스 추가?
→ infrastructure/external_services/에 추가

새로운 로깅 기능?
→ infrastructure/logger/에 추가
```

### **5. 코드 재사용성** ⭐⭐⭐
```
Logger는 모든 계층에서 사용 가능
Cache는 모든 계층에서 사용 가능
Auth는 모든 계층에서 사용 가능
```

---

## 📊 구조 비교

| 항목 | Before | After |
|------|--------|-------|
| **파일 위치** | 혼재 (workflow, utils) | 명확 (infrastructure) |
| **의존성 방향** | 모호함 | 명확함 (단방향) |
| **테스트** | 어려움 | 쉬움 (Mock 주입) |
| **문서화** | 불명확 | 자동으로 명확 |
| **새로운 개발자** | 위치 찾기 어려움 | 직관적 |

---

## 🚀 적용 순서 (권장)

### **Week 1: Infrastructure 기초**
1. 폴더 구조 생성
2. 외부 서비스 파일 이동
3. Import 경로 변경
4. 테스트 실행

### **Week 2: Logger & Cache 추가**
1. Logger 구현 (선택사항)
2. Cache 인터페이스 정의 (선택사항)
3. 문서화 업데이트

### **이후: 점진적 개선**
1. 의존성 주입 적용
2. 거버넌스 자동화 (ArchUnit)
3. 성능 최적화 (캐싱, 비동기)

---

## 💡 결론

**Infrastructure 계층**으로의 변경은:

✅ 아키텍처 명확성 극대화
✅ 테스트 복잡도 감소
✅ 팀 온보딩 용이
✅ 미래 확장성 우수
✅ 책의 레이어드 아키텍처 모범 사례 구현

**추천**: 우선순위 **⭐⭐⭐ 높음** - 지금 바로 시작!

---

**다음 단계**:
1. 이 구조에 동의하면 마이그레이션 스크립트 작성
2. 또는 테스트를 먼저 Infrastructure 기준으로 수정
3. 점진적으로 프로덕션 코드 이동
