# 아키텍처 시각화 & 자동 검증 도구 설정 가이드

**목표**: Mermaid 다이어그램 + 자동 검증 스크립트 설정

---

## 1️⃣ IDE 확장 설치 (VS Code)

### **Mermaid 다이어그램 보기**

#### **Option A: Markdown Preview Mermaid Support (추천) ⭐**

1. **VS Code 확장 마켓플레이스 열기**
   - `Ctrl+Shift+X` (Windows/Linux) 또는 `Cmd+Shift+X` (Mac)

2. **검색**: `Markdown Preview Mermaid Support`

3. **설치** (by Matt Bierner)
   ```
   ms-vscode.markdown-mermaid
   ```

4. **확인**:
   - Markdown 파일 우클릭
   - "Open Preview" 또는 `Ctrl+Shift+V`
   - Mermaid 다이어그램이 렌더링됨 ✅

#### **Option B: Mermaid Markdown Syntax Highlighting**

```
검색: "Mermaid Markdown"
설치: bpruitt-goddard.mermaid-markdown-syntax-highlighting
```

---

## 2️⃣ Python 자동 검증 도구 설치

### **필요한 라이브러리**

```bash
# 프로젝트 폴더에서 실행
cd /home/nadle/para/projects/k-beauty-landing-page/backend

# 1. ast (Python 기본 라이브러리 - 설치 불필요)
# 2. pathlib (Python 기본 라이브러리 - 설치 불필요)

# 3. 고급 검증용 (선택사항)
uv add --dev pylint
uv add --dev prospector

# 또는 requirements.txt에 추가
# pylint==3.0.0
# prospector==1.10.3
```

### **확인**

```bash
# Python import 확인
python -c "import ast, pathlib; print('✅ 기본 도구 OK')"

# pylint 확인 (설치했다면)
pylint --version
```

---

## 3️⃣ 자동 검증 스크립트 생성

### **Step 1: 스크립트 파일 생성**

```bash
mkdir -p /home/nadle/para/projects/k-beauty-landing-page/backend/scripts

touch /home/nadle/para/projects/k-beauty-landing-page/backend/scripts/validate_architecture.py
```

### **Step 2: 스크립트 작성**

```python
#!/usr/bin/env python3
"""아키텍처 규칙 검증 스크립트"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ============================================
# 아키텍처 규칙 정의
# ============================================

ARCHITECTURE_RULES = {
    "presentation": {
        "can_import": ["workflow", "infrastructure"],
        "cannot_import": ["persistence"],
        "description": "Presentation 계층 (폐쇄) - workflow와 infrastructure만 import 가능"
    },
    "workflow": {
        "can_import": ["persistence", "infrastructure"],
        "cannot_import": ["presentation"],
        "description": "Workflow/Business 계층 (폐쇄) - persistence와 infrastructure만 import 가능"
    },
    "persistence": {
        "can_import": ["infrastructure"],
        "cannot_import": ["presentation", "workflow"],
        "description": "Persistence 계층 (폐쇄) - infrastructure만 import 가능"
    },
    "infrastructure": {
        "can_import": ["config"],  # 설정만 가능
        "cannot_import": ["presentation", "workflow", "persistence"],
        "description": "Infrastructure 계층 (개방) - 다른 계층 import 불가"
    },
}

# ============================================
# 스크립트
# ============================================

class ArchitectureValidator:
    """아키텍처 규칙 검증자"""

    def __init__(self, src_path: str = "src"):
        self.src_path = Path(src_path)
        self.violations: List[Dict] = []
        self.files_checked = 0

    def get_layer_from_path(self, file_path: Path) -> str:
        """파일 경로에서 계층 추출"""
        parts = file_path.parts
        if len(parts) > 1:
            return parts[0]  # src 다음 폴더가 계층
        return None

    def extract_imports(self, file_path: Path) -> Set[str]:
        """파일에서 import 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except Exception as e:
            print(f"⚠️ {file_path} 파싱 실패: {e}")
            return set()

        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('src.'):
                    # src.workflow.services → workflow
                    layer = node.module.split('.')[1]
                    imports.add(layer)

        return imports

    def check_file(self, file_path: Path) -> None:
        """단일 파일 검증"""
        if file_path.name.startswith('__'):
            return

        self.files_checked += 1

        # 현재 파일의 계층 판단
        current_layer = self.get_layer_from_path(file_path.relative_to(self.src_path))

        if not current_layer or current_layer not in ARCHITECTURE_RULES:
            return

        # Import 추출
        imports = self.extract_imports(file_path)

        # 규칙 확인
        rules = ARCHITECTURE_RULES[current_layer]

        for imported_layer in imports:
            if imported_layer in rules.get("cannot_import", []):
                self.violations.append({
                    "file": str(file_path),
                    "layer": current_layer,
                    "imported_layer": imported_layer,
                    "rule": f"{current_layer}는 {imported_layer}를 import할 수 없음",
                })

    def validate_all(self) -> None:
        """모든 Python 파일 검증"""
        for py_file in self.src_path.rglob("*.py"):
            self.check_file(py_file)

    def print_report(self) -> None:
        """검증 결과 출력"""
        print("\n" + "="*60)
        print("🏗️ 아키텍처 검증 리포트")
        print("="*60)

        print(f"\n📊 검사한 파일: {self.files_checked}개")

        if not self.violations:
            print("\n✅ 모든 아키텍처 규칙을 준수합니다!")
            self._print_rules()
            return

        print(f"\n❌ 발견된 규칙 위반: {len(self.violations)}개\n")

        for violation in self.violations:
            print(f"📍 파일: {violation['file']}")
            print(f"   계층: {violation['layer']}")
            print(f"   ❌ {violation['rule']}")
            print()

        self._print_rules()

    def _print_rules(self) -> None:
        """현재 규칙 출력"""
        print("\n📋 현재 아키텍처 규칙:")
        print("-" * 60)
        for layer, rules in ARCHITECTURE_RULES.items():
            print(f"\n{layer.upper()}:")
            print(f"  설명: {rules['description']}")
            print(f"  ✅ Import 가능: {', '.join(rules['can_import']) or 'None'}")
            print(f"  ❌ Import 불가: {', '.join(rules['cannot_import']) or 'None'}")

    def exit_code(self) -> int:
        """종료 코드 반환"""
        return 1 if self.violations else 0


def main():
    """메인 함수"""
    print("🔍 아키텍처 검증 시작...\n")

    validator = ArchitectureValidator(src_path="src")
    validator.validate_all()
    validator.print_report()

    exit_code = validator.exit_code()
    if exit_code != 0:
        print(f"\n⚠️ 아키텍처 규칙 위반이 발견되었습니다!")

    return exit_code


if __name__ == "__main__":
    exit(main())
```

### **Step 3: 실행 권한 설정**

```bash
chmod +x scripts/validate_architecture.py
```

---

## 4️⃣ 스크립트 실행 방법

### **방법 1: 직접 실행**

```bash
cd /home/nadle/para/projects/k-beauty-landing-page/backend

# 실행
python scripts/validate_architecture.py

# 또는
./scripts/validate_architecture.py
```

### **방법 2: VS Code 작업(Task)으로 등록**

`.vscode/tasks.json` 생성:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate Architecture",
      "type": "shell",
      "command": "python",
      "args": ["scripts/validate_architecture.py"],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      },
      "problemMatcher": []
    }
  ]
}
```

**실행**:
- `Ctrl+Shift+B` (Windows/Linux) 또는 `Cmd+Shift+B` (Mac)
- "Validate Architecture" 선택

### **방법 3: Pre-commit Hook (Git)**

`.git/hooks/pre-commit` 생성:

```bash
#!/bin/bash
# Git commit 전에 아키텍처 검증 실행

echo "🔍 아키텍처 검증 중..."
python scripts/validate_architecture.py

if [ $? -ne 0 ]; then
  echo "❌ 아키텍처 규칙 위반! Commit 실패"
  exit 1
fi

echo "✅ 아키텍처 검증 통과!"
```

실행 권한 설정:
```bash
chmod +x .git/hooks/pre-commit
```

### **방법 4: pyproject.toml에 스크립트 추가**

```toml
# pyproject.toml
[tool.custom]
validate-architecture = "python scripts/validate_architecture.py"
```

실행:
```bash
uv run validate-architecture
```

---

## 5️⃣ Mermaid 다이어그램 작성

### **Step 1: README.md 또는 docs/ARCHITECTURE.md 생성**

```markdown
# 아키텍처 구조

## 계층 다이어그램

\`\`\`mermaid
graph TB
    subgraph Presentation["📱 Presentation Layer (폐쇄)"]
        Router["HTTP Routers"]
        Schema["Schemas"]
        PresentationExc["Exceptions"]
    end

    subgraph Workflow["⚙️ Workflow/Business Layer (폐쇄)"]
        OrderService["OrderService"]
        AffiliateService["AffiliateService"]
        FulfillmentService["FulfillmentService"]
        ShipmentService["ShipmentService"]
    end

    subgraph Infrastructure["🔧 Infrastructure Layer (개방)"]
        ExternalServices["ExternalServices"]
        Email["EmailService"]
        Payment["PaymentService"]
        Logger["Logger"]
        Cache["Cache"]
        Auth["Auth/JWT"]
    end

    subgraph Persistence["💾 Persistence Layer (폐쇄)"]
        Repository["Repositories"]
        Models["Models"]
    end

    Database[("🗄️ Database")]

    Router -->|호출| OrderService
    OrderService -->|호출| Repository
    OrderService -->|선택적| Email
    OrderService -->|선택적| Payment
    OrderService -->|선택적| Logger
    Repository --> Database

    style Presentation fill:#e1f5ff
    style Workflow fill:#f3e5f5
    style Infrastructure fill:#fff3e0
    style Persistence fill:#e8f5e9
\`\`\`

## 규칙

- Presentation → Workflow (필수)
- Workflow → Persistence (필수)
- 모든 계층 → Infrastructure (선택적)
- 역방향 의존성 금지
\`
```

---

## 6️⃣ 전체 설정 체크리스트

### **IDE 설정**
- [ ] Markdown Preview Mermaid Support 설치
- [ ] VS Code 재시작

### **스크립트 설정**
- [ ] `scripts/validate_architecture.py` 생성
- [ ] 실행 권한 설정 (`chmod +x`)
- [ ] 수동 실행 테스트

### **자동화 설정 (선택)**
- [ ] `.vscode/tasks.json` 생성 (Task 실행용)
- [ ] `.git/hooks/pre-commit` 생성 (자동 검증)
- [ ] `pyproject.toml` 스크립트 추가

### **문서화**
- [ ] `docs/ARCHITECTURE.md` 또는 `README.md`에 다이어그램 추가
- [ ] 계층별 규칙 문서화

---

## 7️⃣ 스크립트 실행 결과 예시

### **✅ 통과한 경우**

```
🔍 아키텍처 검증 시작...

============================================================
🏗️ 아키텍처 검증 리포트
============================================================

📊 검사한 파일: 45개

✅ 모든 아키텍처 규칙을 준수합니다!

📋 현재 아키텍처 규칙:
------------------------------------------------------------

PRESENTATION:
  설명: Presentation 계층 (폐쇄) - workflow와 infrastructure만 import 가능
  ✅ Import 가능: workflow, infrastructure
  ❌ Import 불가: persistence

WORKFLOW:
  설명: Workflow/Business 계층 (폐쇄) - persistence와 infrastructure만 import 가능
  ✅ Import 가능: persistence, infrastructure
  ❌ Import 불가: presentation
...
```

### **❌ 위반 발생한 경우**

```
🔍 아키텍처 검증 시작...

============================================================
🏗️ 아키텍처 검증 리포트
============================================================

📊 검사한 파일: 45개

❌ 발견된 규칙 위반: 2개

📍 파일: src/workflow/services/order_service.py
   계층: workflow
   ❌ workflow는 presentation를 import할 수 없음

📍 파일: src/persistence/repositories/order_repository.py
   계층: persistence
   ❌ persistence는 workflow를 import할 수 없음

⚠️ 아키텍처 규칙 위반이 발견되었습니다!
```

---

## 8️⃣ 자주 하는 실수 & 해결

### **"모듈을 찾을 수 없다" 에러**

```python
# ❌ 이렇게 하면 스크립트가 못 찾음
from src.workflow.services import OrderService

# ✅ 스크립트가 이렇게 된 import를 찾음
import src.workflow.services.order_service
```

### **Python 경로 문제**

```bash
# 스크립트를 backend 폴더에서 실행
cd /home/nadle/para/projects/k-beauty-landing-page/backend
python scripts/validate_architecture.py

# 또는 전체 경로 지정
python /home/nadle/para/projects/k-beauty-landing-page/backend/scripts/validate_architecture.py
```

### **특정 파일 제외하기**

```python
# validate_architecture.py에 추가
EXCLUDE_PATTERNS = [
    "__init__.py",
    "migrations/",
    "tests/",
]

def should_check(file_path: Path) -> bool:
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(file_path):
            return False
    return True
```

---

## 9️⃣ 요약

| 도구 | 설치 | 용도 | 주기 |
|------|------|------|------|
| **Mermaid** | VS Code 확장 | 아키텍처 시각화 | 월 1회 |
| **검증 스크립트** | Python (기본 라이브러리) | 자동 규칙 검증 | 매 commit |
| **Pre-commit Hook** | Git 설정 | 강제 검증 | 자동 |
| **Task** | VS Code 설정 | 수동 검증 | 필요시 |

---

## 🚀 빠른 시작 (5분)

```bash
# 1. VS Code 확장 설치 (GUI에서)
# Marketplace에서 "Markdown Preview Mermaid Support" 설치

# 2. 스크립트 생성
mkdir -p scripts
# validate_architecture.py 코드 붙여넣기

# 3. 테스트 실행
python scripts/validate_architecture.py

# 4. README.md에 Mermaid 다이어그램 추가
```

**완료! 🎉**

이제 매 commit마다 아키텍처가 자동으로 검증됩니다!
