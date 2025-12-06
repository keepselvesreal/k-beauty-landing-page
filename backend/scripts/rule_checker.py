"""
아키텍처 규칙 검증
- 금지된 import 패턴 감지
- 계층 격리 규칙 검증
- 위반 사항 상세 보고
"""

from typing import Dict, List, Tuple
import os


class RuleChecker:
    """아키텍처 규칙 검증"""

    def __init__(self, rules: Dict, analyzer, resolver):
        self.rules = rules
        self.analyzer = analyzer
        self.resolver = resolver
        self.violations: List[Dict] = []

    def check_all(self) -> List[Dict]:
        """모든 규칙 검증"""
        self.violations = []

        # 1. 금지된 import 패턴 검사
        self._check_forbidden_patterns()

        # 2. 순환 의존성 검사
        self._check_circular_dependencies()

        # 3. 계층 격리 검사
        self._check_layer_isolation()

        return self.violations

    def _check_forbidden_patterns(self) -> None:
        """금지된 import 패턴 검증"""
        forbidden_patterns = self.rules.get("import_rules", {}).get(
            "forbidden_patterns", []
        )

        for file_path, dependencies in self.resolver.dependency_graph.items():
            source_layer = self.analyzer.get_layer(file_path)

            for dep_file in dependencies:
                target_layer = self.analyzer.get_layer(dep_file)

                # 금지 패턴 확인
                for pattern in forbidden_patterns:
                    if (
                        pattern.get("from") == source_layer
                        and pattern.get("to") == target_layer
                    ):
                        self.violations.append({
                            "type": "forbidden_import",
                            "severity": pattern.get("severity", "error"),
                            "source_file": file_path,
                            "source_layer": source_layer,
                            "target_file": dep_file,
                            "target_layer": target_layer,
                            "reason": pattern.get("description"),
                            "message": (
                                f"{file_path} ({source_layer}) "
                                f"cannot import from {dep_file} ({target_layer})"
                            ),
                        })

    def _check_circular_dependencies(self) -> None:
        """순환 의존성 검증"""
        if not self.rules.get("circular_dependency_check", {}).get("enabled", False):
            return

        cycles = self.resolver.find_circular_dependencies()

        for cycle in cycles:
            self.violations.append({
                "type": "circular_dependency",
                "severity": "warning",
                "cycle": cycle,
                "message": f"Circular dependency detected: {' -> '.join(cycle)} -> {cycle[0]}",
            })

    def _check_layer_isolation(self) -> None:
        """계층 격리 검증"""
        matrix = self.resolver.get_layer_dependency_matrix()
        layer_config = self.rules.get("layers", {})

        for source_layer, targets in matrix.items():
            if source_layer not in layer_config:
                continue

            allowed_layers = layer_config[source_layer].get("can_import_from", [])

            for target_layer, count in targets.items():
                if count > 0 and target_layer not in allowed_layers:
                    # 해당 위반을 유발하는 파일 찾기
                    for file_path, dependencies in self.resolver.dependency_graph.items():
                        if self.analyzer.get_layer(file_path) != source_layer:
                            continue

                        for dep_file in dependencies:
                            if (
                                self.analyzer.get_layer(dep_file)
                                == target_layer
                            ):
                                self.violations.append({
                                    "type": "layer_isolation",
                                    "severity": "error",
                                    "source_file": file_path,
                                    "source_layer": source_layer,
                                    "target_file": dep_file,
                                    "target_layer": target_layer,
                                    "message": (
                                        f"{source_layer} layer ({file_path}) "
                                        f"cannot import from {target_layer} layer ({dep_file})"
                                    ),
                                })

    def get_violations_by_type(self) -> Dict[str, List[Dict]]:
        """위반 사항을 타입별로 분류"""
        violations_by_type = {}

        for violation in self.violations:
            vtype = violation.get("type", "unknown")
            if vtype not in violations_by_type:
                violations_by_type[vtype] = []

            violations_by_type[vtype].append(violation)

        return violations_by_type

    def get_violations_by_severity(self) -> Dict[str, List[Dict]]:
        """위반 사항을 심각도별로 분류"""
        violations_by_severity = {}

        for violation in self.violations:
            severity = violation.get("severity", "unknown")
            if severity not in violations_by_severity:
                violations_by_severity[severity] = []

            violations_by_severity[severity].append(violation)

        return violations_by_severity

    def get_violations_by_file(self) -> Dict[str, List[Dict]]:
        """파일별 위반 사항"""
        violations_by_file = {}

        for violation in self.violations:
            source_file = violation.get("source_file")

            if source_file:
                if source_file not in violations_by_file:
                    violations_by_file[source_file] = []

                violations_by_file[source_file].append(violation)

        return violations_by_file

    def get_summary(self) -> Dict:
        """위반 사항 요약"""
        by_type = self.get_violations_by_type()
        by_severity = self.get_violations_by_severity()

        return {
            "total_violations": len(self.violations),
            "by_type": {vtype: len(viols) for vtype, viols in by_type.items()},
            "by_severity": {
                severity: len(viols) for severity, viols in by_severity.items()
            },
            "critical_violations": len(by_severity.get("error", [])),
            "warnings": len(by_severity.get("warning", [])),
            "compliance_rate": (
                100.0
                if len(self.violations) == 0
                else 100.0
                * (
                    1.0
                    - len(by_severity.get("error", []))
                    / (
                        len(self.violations)
                        if self.violations
                        else 1
                    )
                )
            ),
        }
