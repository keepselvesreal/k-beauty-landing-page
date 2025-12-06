"""
아키텍처 검증 보고서 자동 생성
- Markdown 형식
- 선택된 다이어그램 수준 포함
- 위반 사항 상세 분석
"""

from datetime import datetime
from typing import Dict, List, Optional
import json


class ReportGenerator:
    """아키텍처 검증 보고서 생성"""

    def __init__(self, analyzer, resolver, rule_checker, diagram_generator):
        self.analyzer = analyzer
        self.resolver = resolver
        self.rule_checker = rule_checker
        self.diagram_generator = diagram_generator

    def generate(
        self,
        diagram_level: str = "3",
        output_file: str = "ARCHITECTURE_VALIDATION_REPORT.md",
        save_diagrams: bool = True,
        diagrams_dir: str = "docs",
    ) -> str:
        """
        보고서 생성

        Args:
            diagram_level: "1", "2", "3", "all", "none"
            output_file: 출력 파일 경로
            save_diagrams: 다이어그램을 별도 파일로 저장할지 여부
            diagrams_dir: 다이어그램 저장 디렉토리

        Returns:
            생성된 보고서 Markdown 문자열
        """
        report = ""

        # 1. Executive Summary
        report += self._generate_executive_summary()

        # 2. 아키텍처 규칙
        report += self._generate_rules_section()

        # 3. Mermaid 다이어그램 (선택된 수준만)
        if save_diagrams:
            report += self._generate_diagrams_section_with_links(
                diagram_level, diagrams_dir
            )
        else:
            report += self._generate_diagrams_section(diagram_level)

        # 4. 의존성 분석
        report += self._generate_dependency_analysis()

        # 5. 위반 사항
        report += self._generate_violations_section()

        # 6. 권장사항
        report += self._generate_recommendations_section()

        # 7. CLI 사용법
        report += self._generate_usage_section()

        # 파일 저장
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        return report

    def _generate_executive_summary(self) -> str:
        """Executive Summary 섹션"""
        summary = self.rule_checker.get_summary()
        files_by_layer = self.analyzer.get_files_by_layer()

        total_files = sum(len(files) for files in files_by_layer.values())
        total_files -= len(files_by_layer.get("unknown", []))

        report = "# 아키텍처 검증 보고서\n\n"
        report += f"**생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "## 📊 Executive Summary\n\n"
        report += (
            f"| 항목 | 값 |\n"
            f"|------|-----|\n"
            f"| 총 파일 수 | {total_files} |\n"
            f"| 위반 규칙 수 | {summary['total_violations']} |\n"
            f"| 심각한 위반 | {summary['critical_violations']} |\n"
            f"| 경고 | {summary['warnings']} |\n"
            f"| 준수율 | {summary['compliance_rate']:.1f}% |\n\n"
        )

        if summary["total_violations"] == 0:
            report += "✅ **모든 아키텍처 규칙을 준수하고 있습니다!**\n\n"
        else:
            report += (
                f"⚠️  **{summary['critical_violations']}개의 규칙 위반이 감지되었습니다.**\n\n"
            )

        return report

    def _generate_rules_section(self) -> str:
        """아키텍처 규칙 섹션"""
        rules = self.rule_checker.rules
        layers = rules.get("layers", {})

        report = "## 🏗️ 아키텍처 규칙\n\n"

        # 계층 설명
        report += "### 계층 정의\n\n"
        report += (
            "| 계층 | 설명 | 유형 |\n"
            "|------|------|------|\n"
        )

        for layer_name, layer_info in layers.items():
            description = layer_info.get("description", "")
            layer_type = layer_info.get("type", "")
            report += f"| {layer_name} | {description} | {layer_type} |\n"

        report += "\n"

        # 의존성 매트릭스
        report += "### 의존성 매트릭스\n\n"
        report += self._generate_dependency_matrix()

        return report

    def _generate_dependency_matrix(self) -> str:
        """의존성 매트릭스 생성"""
        matrix = self.resolver.get_layer_dependency_matrix()
        layers = ["presentation", "workflow", "persistence", "infrastructure"]

        table = "```\n"
        table += "         │ Pres │ Work │ Pers │ Infr │\n"
        table += "─────────┼──────┼──────┼──────┼──────┤\n"

        for source in layers:
            counts = " │ ".join(
                f"{matrix[source].get(target, 0):3d}"
                for target in layers
            )
            table += f"{source:7s} │ {counts} │\n"

        table += "```\n\n"

        table += "✓ = 허용된 의존성\n"
        table += "✗ = 금지된 의존성\n\n"

        return table

    def _generate_diagrams_section(self, diagram_level: str) -> str:
        """다이어그램 섹션 (인라인)"""
        report = "## 📈 아키텍처 다이어그램\n\n"

        if diagram_level == "none":
            report += "다이어그램이 포함되지 않았습니다.\n\n"
            return report

        levels_to_generate = []

        if diagram_level == "1":
            levels_to_generate = [1]
        elif diagram_level == "2":
            levels_to_generate = [2]
        elif diagram_level == "3":
            levels_to_generate = [3]
        elif diagram_level == "all":
            levels_to_generate = [1, 2, 3]

        for level in levels_to_generate:
            if level == 1:
                report += "### Level 1: High-Level Architecture\n\n"
                report += "```mermaid\n"
                report += self.diagram_generator.generate_level1()
                report += "```\n\n"

            elif level == 2:
                report += "### Level 2: Component-Level Architecture\n\n"
                report += "```mermaid\n"
                report += self.diagram_generator.generate_level2()
                report += "```\n\n"

            elif level == 3:
                report += "### Level 3: Detailed Architecture\n\n"
                report += "```mermaid\n"
                report += self.diagram_generator.generate_level3()
                report += "```\n\n"

        return report

    def _generate_diagrams_section_with_links(
        self, diagram_level: str, diagrams_dir: str
    ) -> str:
        """다이어그램 섹션 (별도 파일 링크)"""
        import os
        from pathlib import Path

        report = "## 📈 아키텍처 다이어그램\n\n"

        if diagram_level == "none":
            report += "다이어그램이 포함되지 않았습니다.\n\n"
            return report

        # diagrams_dir 생성
        Path(diagrams_dir).mkdir(parents=True, exist_ok=True)

        levels_to_generate = []

        if diagram_level == "1":
            levels_to_generate = [1]
        elif diagram_level == "2":
            levels_to_generate = [2]
        elif diagram_level == "3":
            levels_to_generate = [3]
        elif diagram_level == "all":
            levels_to_generate = [1, 2, 3]

        for level in levels_to_generate:
            if level == 1:
                diagram_file = f"{diagrams_dir}/architecture_level1.md"
                diagram_content = self.diagram_generator.generate_level1()
                self._save_diagram_file(
                    diagram_file, diagram_content, "Level 1: High-Level Architecture"
                )
                report += f"### Level 1: High-Level Architecture\n\n"
                report += f"[📄 View Diagram](architecture_level1.md)\n\n"

            elif level == 2:
                diagram_file = f"{diagrams_dir}/architecture_level2.md"
                diagram_content = self.diagram_generator.generate_level2()
                self._save_diagram_file(
                    diagram_file, diagram_content, "Level 2: Component-Level Architecture"
                )
                report += f"### Level 2: Component-Level Architecture\n\n"
                report += f"[📄 View Diagram](architecture_level2.md)\n\n"

            elif level == 3:
                report += f"### Level 3: Detailed Architecture\n\n"

                # 섹션별 다이어그램 생성
                sectioned_diagrams = (
                    self.diagram_generator.generate_level3_by_layer()
                )

                sections = [
                    ("presentation_to_workflow", "🎨 Presentation → 💼 Workflow"),
                    ("workflow_to_persistence", "💼 Workflow → 💾 Persistence"),
                    ("workflow_to_infrastructure", "💼 Workflow → ⚙️ Infrastructure"),
                    ("persistence_internal", "💾 Persistence Internal Structure"),
                ]

                for section_key, section_title in sections:
                    if section_key in sectioned_diagrams:
                        diagram_file = (
                            f"{diagrams_dir}/architecture_level3_{section_key}.md"
                        )
                        diagram_content = sectioned_diagrams[section_key]
                        self._save_diagram_file(
                            diagram_file,
                            diagram_content,
                            f"Level 3: {section_title}",
                        )
                        report += f"#### {section_title}\n\n"
                        report += (
                            f"[📄 View Diagram](architecture_level3_{section_key}.md)\n\n"
                        )

        return report

    def _save_diagram_file(
        self, file_path: str, diagram_content: str, title: str
    ) -> None:
        """다이어그램을 별도 파일로 저장"""
        content = f"# {title}\n\n"
        content += f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "```mermaid\n"
        content += diagram_content
        content += "```\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_dependency_analysis(self) -> str:
        """의존성 분석 섹션"""
        report = "## 📊 의존성 분석\n\n"

        # 가장 많이 import되는 파일
        report += "### 가장 많이 Import되는 파일\n\n"
        most_imported = self.resolver.get_most_imported_files(top_n=5)

        if most_imported:
            report += "```\n"
            for file_path, count in most_imported:
                report += f"{count:3d}회 - {file_path}\n"
            report += "```\n\n"

        # 가장 많이 의존하는 파일
        report += "### 가장 많이 의존하는 파일\n\n"
        most_dependent = self.resolver.get_most_dependent_files(top_n=5)

        if most_dependent:
            report += "```\n"
            for file_path, count in most_dependent:
                report += f"{count:3d}개 import - {file_path}\n"
            report += "```\n\n"

        # 계층별 통계
        report += "### 계층별 통계\n\n"
        files_by_layer = self.analyzer.get_files_by_layer()
        import_count = self.resolver.get_import_count_by_layer()

        report += (
            "| 계층 | 파일 수 | Import 수 |\n"
            "|------|---------|----------|\n"
        )

        for layer in ["presentation", "workflow", "persistence", "infrastructure"]:
            file_count = len(files_by_layer.get(layer, []))
            import_cnt = import_count.get(layer, 0)
            report += f"| {layer} | {file_count} | {import_cnt} |\n"

        report += "\n"

        return report

    def _generate_violations_section(self) -> str:
        """위반 사항 섹션"""
        report = "## ⚠️ 위반 사항\n\n"

        if not self.rule_checker.violations:
            report += "✅ **위반 사항이 없습니다!**\n\n"
            return report

        # 타입별 위반
        violations_by_type = self.rule_checker.get_violations_by_type()

        for vtype, violations in violations_by_type.items():
            report += f"### {vtype.upper()} ({len(violations)}건)\n\n"

            for violation in violations[:10]:  # 최대 10개만 표시
                source = violation.get("source_file", "Unknown")
                target = violation.get("target_file", "Unknown")
                reason = violation.get("reason", "")

                report += f"- **{source}** → {target}\n"
                report += f"  - 사유: {reason}\n\n"

            if len(violations) > 10:
                report += f"... 외 {len(violations) - 10}건\n\n"

        return report

    def _generate_recommendations_section(self) -> str:
        """권장사항 섹션"""
        report = "## 💡 권장사항\n\n"

        summary = self.rule_checker.get_summary()

        if summary["total_violations"] == 0:
            report += (
                "### 현재 상태\n"
                "- ✅ 모든 아키텍처 규칙을 준수하고 있습니다.\n"
                "- ✅ 계층 격리가 잘 유지되고 있습니다.\n"
                "- ✅ 순환 의존성이 없습니다.\n\n"
            )

            report += (
                "### 유지 및 개선\n"
                "1. 정기적인 아키텍처 검증 실행 (CI/CD에 통합)\n"
                "2. Pre-commit hook으로 실시간 검증\n"
                "3. 새로운 기능 추가 시 아키텍처 규칙 확인\n\n"
            )
        else:
            report += (
                "### 개선 필요 사항\n"
                "1. 위반 사항에 나열된 파일들의 import 관계 수정\n"
                "2. 금지된 계층 간 의존성 제거\n"
                "3. 순환 의존성 해결\n\n"
            )

            report += (
                "### 해결 방법\n"
                "- **의존성 역전**: 의존성의 방향을 바꾸기\n"
                "- **인터페이스 분리**: Protocol을 이용한 추상화\n"
                "- **계층 이동**: 모듈을 다른 계층으로 이동\n\n"
            )

        return report

    def _generate_usage_section(self) -> str:
        """CLI 사용법 섹션"""
        report = "## 🔧 CLI 사용법\n\n"

        report += (
            "```bash\n"
            "# 기본 검증 (콘솔 출력)\n"
            "python scripts/validate_architecture.py\n\n"
            "# 보고서 생성 (Level 3 다이어그램 포함, 기본)\n"
            "python scripts/validate_architecture.py --report\n\n"
            "# Level 1 다이어그램 포함\n"
            "python scripts/validate_architecture.py --report --diagram-level 1\n\n"
            "# Level 2 다이어그램 포함\n"
            "python scripts/validate_architecture.py --report --diagram-level 2\n\n"
            "# 모든 Level 다이어그램 포함\n"
            "python scripts/validate_architecture.py --report --diagram-level all\n\n"
            "# 다이어그램 없이 (규칙 & 위반사항만)\n"
            "python scripts/validate_architecture.py --report --diagram-level none\n\n"
            "# JSON 형식 출력\n"
            "python scripts/validate_architecture.py --json\n\n"
            "# 콘솔에서 보고서 확인\n"
            "python scripts/validate_architecture.py --report --show\n"
            "```\n\n"
        )

        return report
