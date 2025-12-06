# 아키텍처 검증 보고서

**생성일**: 2025-12-06 12:38:24

## 📊 Executive Summary

| 항목 | 값 |
|------|-----|
| 총 파일 수 | 60 |
| 위반 규칙 수 | 43 |
| 심각한 위반 | 43 |
| 경고 | 0 |
| 준수율 | 0.0% |

⚠️  **43개의 규칙 위반이 감지되었습니다.**

## 🏗️ 아키텍처 규칙

### 계층 정의

| 계층 | 설명 | 유형 |
|------|------|------|
| presentation | HTTP 요청/응답 처리, 스키마, 검증 | closed |
| workflow | 순수 비즈니스 로직, 서비스, 도메인 모델 | closed |
| persistence | 데이터베이스 접근, 리포지토리, ORM 모델 | closed |
| infrastructure | 외부 서비스, 로깅, 인증, 캐싱 등 기술적 기능 | open |

### 의존성 매트릭스

```
         │ Pres │ Work │ Pers │ Infr │
─────────┼──────┼──────┼──────┼──────┤
presentation │   7 │   5 │  13 │   3 │
workflow │   0 │   3 │  11 │   2 │
persistence │   0 │   1 │   9 │   0 │
infrastructure │   0 │   0 │   3 │   2 │
```

✓ = 허용된 의존성
✗ = 금지된 의존성

## 📈 아키텍처 다이어그램

### Level 3: Detailed Architecture

#### 🎨 Presentation → 💼 Workflow

[📄 View Diagram](architecture_level3_presentation_to_workflow.md)

#### 💼 Workflow → 💾 Persistence

[📄 View Diagram](architecture_level3_workflow_to_persistence.md)

#### 💼 Workflow → ⚙️ Infrastructure

[📄 View Diagram](architecture_level3_workflow_to_infrastructure.md)

#### 💾 Persistence Internal Structure

[📄 View Diagram](architecture_level3_persistence_internal.md)

## 📊 의존성 분석

### 가장 많이 Import되는 파일

```
 17회 - persistence/models.py
  7회 - config.py
  7회 - persistence/database.py
  7회 - infrastructure/exceptions.py
  6회 - workflow/exceptions.py
```

### 가장 많이 의존하는 파일

```
  8개 import - workflow/services/order_service.py
  8개 import - presentation/http/routers/fulfillment_partner.py
  5개 import - presentation/http/routers/orders.py
  5개 import - presentation/http/routers/influencer.py
  5개 import - presentation/http/routers/inquiry.py
```

### 계층별 통계

| 계층 | 파일 수 | Import 수 |
|------|---------|----------|
| presentation | 22 | 29 |
| workflow | 13 | 17 |
| persistence | 13 | 11 |
| infrastructure | 10 | 8 |

## ⚠️ 위반 사항

### FORBIDDEN_IMPORT (4건)

- **infrastructure/external_services/email_service.py** → persistence/models.py
  - 사유: Infrastructure이 Persistence의 데이터 접근 로직 호출 금지

- **infrastructure/external_services/email_service.py** → persistence/repositories/email_log_repository.py
  - 사유: Infrastructure이 Persistence의 데이터 접근 로직 호출 금지

- **infrastructure/external_services/interfaces.py** → persistence/models.py
  - 사유: Infrastructure이 Persistence의 데이터 접근 로직 호출 금지

- **persistence/repositories/inventory_repository.py** → workflow/exceptions.py
  - 사유: Persistence이 Workflow의 비즈니스 로직 호출 금지

### LAYER_ISOLATION (39건)

- **presentation/http/routers/orders.py** → presentation/schemas/orders.py
  - 사유: 

- **presentation/http/routers/shipping.py** → presentation/schemas/shipping.py
  - 사유: 

- **presentation/http/routers/influencer.py** → presentation/schemas/influencer.py
  - 사유: 

- **presentation/http/routers/customers.py** → presentation/schemas/customers.py
  - 사유: 

- **presentation/http/routers/inquiry.py** → presentation/schemas/inquiry.py
  - 사유: 

- **presentation/http/routers/fulfillment_partner.py** → presentation/schemas/admin.py
  - 사유: 

- **presentation/http/routers/fulfillment_partner.py** → presentation/schemas/fulfillment_partner.py
  - 사유: 

- **presentation/http/routers/orders.py** → persistence/repositories/order_repository.py
  - 사유: 

- **presentation/http/routers/orders.py** → persistence/database.py
  - 사유: 

- **presentation/http/routers/shipping.py** → persistence/repositories/shipping_repository.py
  - 사유: 

... 외 29건

## 💡 권장사항

### 개선 필요 사항
1. 위반 사항에 나열된 파일들의 import 관계 수정
2. 금지된 계층 간 의존성 제거
3. 순환 의존성 해결

### 해결 방법
- **의존성 역전**: 의존성의 방향을 바꾸기
- **인터페이스 분리**: Protocol을 이용한 추상화
- **계층 이동**: 모듈을 다른 계층으로 이동

## 🔧 CLI 사용법

```bash
# 기본 검증 (콘솔 출력)
python scripts/validate_architecture.py

# 보고서 생성 (Level 3 다이어그램 포함, 기본)
python scripts/validate_architecture.py --report

# Level 1 다이어그램 포함
python scripts/validate_architecture.py --report --diagram-level 1

# Level 2 다이어그램 포함
python scripts/validate_architecture.py --report --diagram-level 2

# 모든 Level 다이어그램 포함
python scripts/validate_architecture.py --report --diagram-level all

# 다이어그램 없이 (규칙 & 위반사항만)
python scripts/validate_architecture.py --report --diagram-level none

# JSON 형식 출력
python scripts/validate_architecture.py --json

# 콘솔에서 보고서 확인
python scripts/validate_architecture.py --report --show
```

