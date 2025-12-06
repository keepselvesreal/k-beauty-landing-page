"""
의존성 그래프 생성 및 분석
- 모듈 간 의존성 관계 해석
- 순환 의존성 감지
- 의존성 경로 추적
"""

import os
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque


class DependencyResolver:
    """의존성 분석 및 해석"""

    def __init__(self, files_info: Dict, analyzer):
        self.files_info = files_info
        self.analyzer = analyzer
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.layer_dependency: Dict[str, Set[str]] = defaultdict(set)

    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """의존성 그래프 생성"""
        for file_path, info in self.files_info.items():
            local_imports = self._extract_local_imports(info["imports"])

            for imported_file in local_imports:
                self.dependency_graph[file_path].add(imported_file)
                # 계층 간 의존성도 기록
                source_layer = self.analyzer.get_layer(file_path)
                target_layer = self.analyzer.get_layer(imported_file)
                if source_layer != target_layer:
                    self.layer_dependency[source_layer].add(target_layer)

        return self.dependency_graph

    def _extract_local_imports(self, imports: List[Dict]) -> Set[str]:
        """
        import 목록에서 로컬 모듈만 추출
        예: 'src.workflow.services.order_service' -> 'workflow/services/order_service.py'
        """
        local_imports = set()

        for imp in imports:
            module_name = imp.get("module", "")

            # 'src.'로 시작하는 것만 처리
            if module_name.startswith("src."):
                # 'src.workflow.services' -> 'workflow/services.py'
                local_path = module_name[4:].replace(".", os.sep) + ".py"

                # 해당 파일이 존재하는지 확인
                if local_path in self.files_info:
                    local_imports.add(local_path)

        return local_imports

    def find_circular_dependencies(self) -> List[List[str]]:
        """순환 의존성 찾기 (깊이 3 제한)"""
        cycles = []
        visited = set()

        for start_node in self.dependency_graph:
            if start_node in visited:
                continue

            cycle = self._find_cycle_from_node(start_node, depth=3)
            if cycle:
                cycles.append(cycle)
                visited.update(cycle)

        return cycles

    def _find_cycle_from_node(
        self, start: str, depth: int = 3
    ) -> List[str]:
        """DFS를 이용한 순환 의존성 감지"""
        visited = set()
        path = []

        def dfs(node: str, target: str, current_depth: int) -> bool:
            if current_depth == 0:
                return False

            if node in visited:
                return False

            visited.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, []):
                if neighbor == target and len(path) > 1:
                    return True

                if dfs(neighbor, target, current_depth - 1):
                    return True

            path.pop()
            return False

        if dfs(start, start, depth):
            return path

        return []

    def get_dependency_chain(self, source: str, target: str) -> List[str]:
        """source에서 target까지의 의존성 경로 찾기"""
        if source not in self.files_info or target not in self.files_info:
            return []

        visited = set()
        queue = deque([(source, [source])])

        while queue:
            current, path = queue.popleft()

            if current == target:
                return path

            if current in visited:
                continue

            visited.add(current)

            for neighbor in self.dependency_graph.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return []

    def get_layer_dependency_matrix(self) -> Dict[str, Dict[str, int]]:
        """계층 간 의존성 매트릭스"""
        layers = ["presentation", "workflow", "persistence", "infrastructure", "external"]
        matrix = {layer: {l: 0 for l in layers} for layer in layers}

        for file_path, dependencies in self.dependency_graph.items():
            source_layer = self.analyzer.get_layer(file_path)

            for dep_file in dependencies:
                target_layer = self.analyzer.get_layer(dep_file)
                matrix[source_layer][target_layer] += 1

        return matrix

    def get_import_count_by_layer(self) -> Dict[str, int]:
        """계층별 import 수"""
        count = defaultdict(int)

        for file_path, dependencies in self.dependency_graph.items():
            source_layer = self.analyzer.get_layer(file_path)
            count[source_layer] += len(dependencies)

        return dict(count)

    def get_most_imported_files(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """가장 많이 import되는 파일 TOP N"""
        import_count = defaultdict(int)

        for dependencies in self.dependency_graph.values():
            for dep in dependencies:
                import_count[dep] += 1

        return sorted(import_count.items(), key=lambda x: x[1], reverse=True)[
            :top_n
        ]

    def get_most_dependent_files(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """가장 많이 의존하는 파일 TOP N"""
        depend_count = {
            file: len(deps) for file, deps in self.dependency_graph.items()
        }

        return sorted(depend_count.items(), key=lambda x: x[1], reverse=True)[
            :top_n
        ]
