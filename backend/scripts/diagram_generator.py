"""
Mermaid 다이어그램 생성
- Level 1: High-Level (계층만)
- Level 2: Component-Level (패키지)
- Level 3: Detailed (파일/함수)
"""

from typing import Dict, List, Set
import json


class DiagramGenerator:
    """Mermaid 다이어그램 생성"""

    def __init__(self, files_info: Dict, analyzer, resolver):
        self.files_info = files_info
        self.analyzer = analyzer
        self.resolver = resolver

    def generate_level1(self) -> str:
        """Level 1: High-Level (계층만)"""
        diagram = "graph TB\n"

        layers = {
            "presentation": "🎨 PRESENTATION<br/>(HTTP Layer)",
            "workflow": "💼 WORKFLOW<br/>(Business Logic)",
            "persistence": "💾 PERSISTENCE<br/>(Data Access)",
            "infrastructure": "⚙️ INFRASTRUCTURE<br/>(Tech Services)",
        }

        # 노드 생성
        for layer, label in layers.items():
            diagram += f'    {layer}["{label}"]\n'

        diagram += "\n"

        # 의존성 추가
        layer_deps = self.resolver.layer_dependency

        if "presentation" in layer_deps:
            for target in layer_deps["presentation"]:
                if target in layers:
                    diagram += f"    presentation --> {target}\n"

        if "workflow" in layer_deps:
            for target in layer_deps["workflow"]:
                if target in layers:
                    diagram += f"    workflow --> {target}\n"

        if "persistence" in layer_deps:
            for target in layer_deps["persistence"]:
                if target in layers:
                    diagram += f"    persistence --> {target}\n"

        # 스타일
        diagram += "\n"
        diagram += '    style presentation fill:#e8f4f8\n'
        diagram += '    style workflow fill:#fff4e8\n'
        diagram += '    style persistence fill:#f4e8ff\n'
        diagram += '    style infrastructure fill:#e8ffe8\n'

        return diagram

    def generate_level2(self) -> str:
        """Level 2: Component-Level (패키지)"""
        diagram = "graph TB\n"

        # 계층별 서브그래프
        subgraphs = self._build_subgraphs()

        for layer, subgraph_content in subgraphs.items():
            diagram += subgraph_content

        # 계층 간 의존성
        diagram += "\n    %% Layer Dependencies\n"
        layer_deps = self.resolver.layer_dependency

        if "presentation" in layer_deps:
            for target in layer_deps["presentation"]:
                if target in subgraphs:
                    diagram += (
                        f"    presentation_pkg1 --> {target}_pkg1\n"
                    )

        if "workflow" in layer_deps:
            for target in layer_deps["workflow"]:
                if target in subgraphs:
                    diagram += (
                        f"    workflow_pkg1 --> {target}_pkg1\n"
                    )

        if "persistence" in layer_deps:
            for target in layer_deps["persistence"]:
                if target in subgraphs:
                    diagram += (
                        f"    persistence_pkg1 --> {target}_pkg1\n"
                    )

        return diagram

    def generate_level3(self) -> str:
        """
        Level 3: Detailed (파일/함수)
        주요 파일과 함수 관계를 상세히 표시
        """
        diagram = "graph TB\n"

        # 주요 서비스 파일 선정
        main_files = self._select_main_files()

        # 노드 생성
        for file_path, info in main_files.items():
            node_id = self._file_to_node_id(file_path)
            short_name = file_path.split("/")[-1].replace(".py", "")
            functions = info.get("functions", [])[:3]  # 상위 3개 함수만
            func_text = "<br/>".join(functions) if functions else ""

            label = f"{short_name}<br/><sub>{func_text}</sub>"
            diagram += f'    {node_id}["{label}"]\n'

        # 의존성 추가
        for source_file, target_files in self.resolver.dependency_graph.items():
            if source_file not in main_files:
                continue

            source_id = self._file_to_node_id(source_file)

            for target_file in target_files:
                if target_file not in main_files:
                    continue

                target_id = self._file_to_node_id(target_file)
                source_layer = self.analyzer.get_layer(source_file)
                target_layer = self.analyzer.get_layer(target_file)

                # 계층을 넘는 의존성은 명확히 표시
                if source_layer != target_layer:
                    diagram += (
                        f'    {source_id} -->|{source_layer} to {target_layer}| '
                        f'{target_id}\n'
                    )
                else:
                    diagram += f"    {source_id} --> {target_id}\n"

        # 스타일
        diagram += "\n"

        for layer, color in [
            ("presentation", "#e8f4f8"),
            ("workflow", "#fff4e8"),
            ("persistence", "#f4e8ff"),
            ("infrastructure", "#e8ffe8"),
        ]:
            for file_path in main_files.keys():
                if self.analyzer.get_layer(file_path) == layer:
                    node_id = self._file_to_node_id(file_path)
                    diagram += f'    style {node_id} fill:{color}\n'

        return diagram

    def generate_level3_by_layer(self) -> Dict[str, str]:
        """
        Level 3: 계층별로 분할된 Detailed 다이어그램
        각 계층의 주요 상호작용을 별도 다이어그램으로 표시
        """
        diagrams = {}

        # Presentation → Workflow
        diagrams["presentation_to_workflow"] = (
            self._generate_layer_interaction_diagram(
                "presentation", "workflow", "🎨 Presentation → 💼 Workflow"
            )
        )

        # Workflow → Persistence
        diagrams["workflow_to_persistence"] = (
            self._generate_layer_interaction_diagram(
                "workflow", "persistence", "💼 Workflow → 💾 Persistence"
            )
        )

        # Workflow → Infrastructure
        diagrams["workflow_to_infrastructure"] = (
            self._generate_layer_interaction_diagram(
                "workflow", "infrastructure", "💼 Workflow → ⚙️ Infrastructure"
            )
        )

        # Persistence → Database
        diagrams["persistence_internal"] = (
            self._generate_persistence_detail_diagram()
        )

        return diagrams

    def _generate_layer_interaction_diagram(
        self, source_layer: str, target_layer: str, title: str
    ) -> str:
        """계층 간 상호작용 다이어그램 생성"""
        diagram = "graph LR\n"

        # 소스 계층 파일
        source_files = self.analyzer.get_files_by_layer().get(source_layer, [])
        # 타겟 계층 파일
        target_files = self.analyzer.get_files_by_layer().get(target_layer, [])

        # 실제 의존성이 있는 파일만 선정
        relevant_source = set()
        relevant_target = set()

        for source_file in source_files:
            for target_file in self.resolver.dependency_graph.get(source_file, []):
                if target_file in target_files:
                    relevant_source.add(source_file)
                    relevant_target.add(target_file)

        # 소스 레이어 노드
        diagram += f'\n    subgraph src["{source_layer.upper()}"]\n'
        for file_path in sorted(list(relevant_source))[:10]:  # 최대 10개
            node_id = self._file_to_node_id(file_path)
            short_name = file_path.split("/")[-1].replace(".py", "")
            functions = self.files_info.get(file_path, {}).get("functions", [])[:2]
            func_text = "<br/>".join(functions) if functions else ""
            label = f"{short_name}<br/><sub>{func_text}</sub>"
            diagram += f'        {node_id}["{label}"]\n'
        diagram += "    end\n"

        # 타겟 레이어 노드
        diagram += f'\n    subgraph tgt["{target_layer.upper()}"]\n'
        for file_path in sorted(list(relevant_target))[:10]:  # 최대 10개
            node_id = self._file_to_node_id(file_path)
            short_name = file_path.split("/")[-1].replace(".py", "")
            functions = self.files_info.get(file_path, {}).get("functions", [])[:2]
            func_text = "<br/>".join(functions) if functions else ""
            label = f"{short_name}<br/><sub>{func_text}</sub>"
            diagram += f'        {node_id}["{label}"]\n'
        diagram += "    end\n"

        # 의존성 화살표
        diagram += "\n"
        for source_file in relevant_source:
            source_id = self._file_to_node_id(source_file)
            for target_file in self.resolver.dependency_graph.get(source_file, []):
                if target_file in relevant_target:
                    target_id = self._file_to_node_id(target_file)
                    diagram += f"    {source_id} --> {target_id}\n"

        # 스타일
        diagram += "\n"
        layer_colors = {
            "presentation": "#e8f4f8",
            "workflow": "#fff4e8",
            "persistence": "#f4e8ff",
            "infrastructure": "#e8ffe8",
        }

        for file_path in relevant_source:
            node_id = self._file_to_node_id(file_path)
            color = layer_colors.get(source_layer, "#ffffff")
            diagram += f'    style {node_id} fill:{color}\n'

        for file_path in relevant_target:
            node_id = self._file_to_node_id(file_path)
            color = layer_colors.get(target_layer, "#ffffff")
            diagram += f'    style {node_id} fill:{color}\n'

        diagram += f'    style src fill:{layer_colors.get(source_layer, "#ffffff")}22\n'
        diagram += f'    style tgt fill:{layer_colors.get(target_layer, "#ffffff")}22\n'

        return diagram

    def _generate_persistence_detail_diagram(self) -> str:
        """Persistence 계층 상세 다이어그램"""
        diagram = "graph TB\n"

        persistence_files = self.analyzer.get_files_by_layer().get(
            "persistence", []
        )

        # 리포지토리 파일들
        diagram += '    subgraph repos["Repositories"]\n'
        repo_count = 0
        for file_path in persistence_files:
            if "repositories" in file_path and repo_count < 8:
                node_id = self._file_to_node_id(file_path)
                short_name = file_path.split("/")[-1].replace("_repository.py", "")
                diagram += f'        {node_id}["{short_name}"]\n'
                repo_count += 1
        diagram += "    end\n"

        # 모델 파일
        diagram += '    subgraph models["Models & Database"]\n'
        for file_path in persistence_files:
            if file_path.endswith(("models.py", "database.py")):
                node_id = self._file_to_node_id(file_path)
                short_name = file_path.split("/")[-1].replace(".py", "")
                diagram += f'        {node_id}["{short_name}"]\n'
        diagram += "    end\n"

        # 의존성
        diagram += "\n"
        for source_file in persistence_files:
            if "repositories" not in source_file:
                continue

            source_id = self._file_to_node_id(source_file)

            for target_file in self.resolver.dependency_graph.get(source_file, []):
                if target_file in persistence_files and target_file.endswith(
                    ("models.py", "database.py")
                ):
                    target_id = self._file_to_node_id(target_file)
                    diagram += f"    {source_id} --> {target_id}\n"

        # 스타일
        diagram += "\n"
        for file_path in persistence_files:
            node_id = self._file_to_node_id(file_path)
            diagram += f'    style {node_id} fill:#f4e8ff\n'

        return diagram

    def _build_subgraphs(self) -> Dict[str, str]:
        """계층별 서브그래프 생성"""
        subgraphs = {}
        layers = self.analyzer.get_files_by_layer()

        for layer, files in layers.items():
            if not files:
                continue

            subgraph = f'    subgraph {layer}["📦 {layer.upper()}"]\n'

            # 폴더별 그룹화
            folders = {}
            for file_path in files:
                parts = file_path.split("/")
                folder = parts[0] if len(parts) > 1 else "root"

                if folder not in folders:
                    folders[folder] = []

                folders[folder].append(file_path)

            # 폴더별 노드 추가
            for folder, file_list in folders.items():
                for file_path in file_list[:5]:  # 폴더당 최대 5개 파일
                    node_id = f"{layer}_{folder}_{len(file_list)}"
                    short_name = file_path.split("/")[-1]
                    subgraph += (
                        f'        {node_id}["{short_name}"]\n'
                    )

            subgraph += "    end\n"
            subgraphs[layer] = subgraph

        return subgraphs

    def _select_main_files(self) -> Dict[str, Dict]:
        """분석할 주요 파일 선정"""
        important_patterns = [
            "services/",
            "repositories/",
            "models.py",
            "database.py",
            "external_services/",
            "auth/",
        ]

        main_files = {}

        for file_path, info in self.files_info.items():
            # 주요 패턴에 해당하는 파일만 선정
            if any(pattern in file_path for pattern in important_patterns):
                main_files[file_path] = info

        # 크기 제한 (최대 20개)
        if len(main_files) > 20:
            # 가장 의존성이 많은 파일 선정
            main_files = dict(
                sorted(
                    main_files.items(),
                    key=lambda x: len(
                        self.resolver.dependency_graph.get(x[0], [])
                    ),
                    reverse=True,
                )[:20]
            )

        return main_files

    def _file_to_node_id(self, file_path: str) -> str:
        """파일 경로를 Mermaid 노드 ID로 변환"""
        # 특수 문자 제거 및 underscode로 변환
        node_id = file_path.replace("/", "_").replace(".", "_").replace("-", "_")
        return node_id
