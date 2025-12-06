"""
AST를 이용한 Python 코드 분석
- 모든 Python 파일의 import 문 추출
- 파일 정보 수집 (크기, 줄 수, 함수 수 등)
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ImportVisitor(ast.NodeVisitor):
    """AST 방문자: import 문 추출"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: List[Dict] = []
        self.functions: List[str] = []
        self.classes: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """from X import Y 형태 처리"""
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "type": "import",
                "line": node.lineno,
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """import X from Y 형태 처리"""
        if node.module:
            self.imports.append({
                "module": node.module,
                "type": "from",
                "names": [alias.name for alias in node.names],
                "line": node.lineno,
            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """함수 정의 수집"""
        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """클래스 정의 수집"""
        self.classes.append(node.name)
        self.generic_visit(node)


class ASTAnalyzer:
    """Python 코드 AST 분석"""

    def __init__(self, root_path: str = "src"):
        self.root_path = Path(root_path)
        self.files_info: Dict[str, Dict] = {}

    def analyze(self) -> Dict:
        """프로젝트 전체 분석"""
        for py_file in self.root_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            self._analyze_file(py_file)

        return self.files_info

    def _analyze_file(self, file_path: Path) -> None:
        """단일 파일 분석"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            visitor = ImportVisitor(str(file_path))
            visitor.visit(tree)

            # 상대 경로 생성
            relative_path = str(file_path.relative_to(self.root_path))

            self.files_info[relative_path] = {
                "absolute_path": str(file_path),
                "relative_path": relative_path,
                "imports": visitor.imports,
                "functions": visitor.functions,
                "classes": visitor.classes,
                "lines_of_code": len(content.splitlines()),
                "file_size": len(content),
            }

        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")

    def get_file_info(self, file_path: str) -> Dict:
        """파일 정보 조회"""
        return self.files_info.get(file_path, {})

    def get_all_imports(self) -> Dict[str, List[Dict]]:
        """모든 import 정보 반환"""
        return {
            file: info["imports"]
            for file, info in self.files_info.items()
        }

    def get_layer(self, file_path: str) -> str:
        """파일 경로에서 계층 추출"""
        path_parts = file_path.split(os.sep)

        # 폴더 기반 계층 판단
        if len(path_parts) > 0:
            first_dir = path_parts[0]

            if first_dir in ["presentation"]:
                return "presentation"
            elif first_dir in ["workflow"]:
                return "workflow"
            elif first_dir in ["persistence"]:
                return "persistence"
            elif first_dir in ["infrastructure"]:
                return "infrastructure"

        # 특수한 경우
        if file_path in ["config.py", "main.py"]:
            return "external"

        return "unknown"

    def get_files_by_layer(self) -> Dict[str, List[str]]:
        """계층별 파일 목록"""
        layers = {
            "presentation": [],
            "workflow": [],
            "persistence": [],
            "infrastructure": [],
            "external": [],
            "unknown": [],
        }

        for file_path in self.files_info.keys():
            layer = self.get_layer(file_path)
            layers[layer].append(file_path)

        return layers
