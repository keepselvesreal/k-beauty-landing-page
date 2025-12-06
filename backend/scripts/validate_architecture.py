#!/usr/bin/env python3
"""
아키텍처 검증 도구 - 메인 CLI
- Python 코드 분석
- 아키텍처 규칙 검증
- Mermaid 다이어그램 생성
- 보고서 자동 생성

사용법:
    python scripts/validate_architecture.py
    python scripts/validate_architecture.py --report
    python scripts/validate_architecture.py --report --diagram-level 3
    python scripts/validate_architecture.py --json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 현재 스크립트 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from ast_analyzer import ASTAnalyzer
from dependency_resolver import DependencyResolver
from rule_checker import RuleChecker
from diagram_generator import DiagramGenerator
from report_generator import ReportGenerator


def load_rules(rules_file: str) -> dict:
    """규칙 파일 로드"""
    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 규칙 파일을 찾을 수 없습니다: {rules_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ 규칙 파일이 유효한 JSON이 아닙니다: {rules_file}")
        sys.exit(1)


def print_console_summary(analyzer, resolver, rule_checker):
    """콘솔 요약 출력"""
    print("\n" + "=" * 80)
    print("🔍 아키텍처 검증 결과")
    print("=" * 80 + "\n")

    files_by_layer = analyzer.get_files_by_layer()
    summary = rule_checker.get_summary()

    # 파일 통계
    print("📊 파일 통계:")
    for layer in ["presentation", "workflow", "persistence", "infrastructure"]:
        count = len(files_by_layer.get(layer, []))
        print(f"  {layer:15s}: {count:3d}개")

    print("\n" + "-" * 80)

    # 의존성 통계
    import_count = resolver.get_import_count_by_layer()
    print("\n📈 의존성 통계:")
    for layer in ["presentation", "workflow", "persistence", "infrastructure"]:
        count = import_count.get(layer, 0)
        print(f"  {layer:15s}: {count:3d}개")

    print("\n" + "-" * 80)

    # 규칙 준수 현황
    print(f"\n✅ 규칙 준수율: {summary['compliance_rate']:.1f}%")
    print(f"⚠️  위반 사항: {summary['total_violations']}건")
    print(f"  - 심각한 위반: {summary['critical_violations']}건")
    print(f"  - 경고: {summary['warnings']}건")

    if summary["total_violations"] > 0:
        print("\n⚠️  위반 사항 상세:")
        violations_by_type = rule_checker.get_violations_by_type()
        for vtype, violations in violations_by_type.items():
            print(f"  {vtype}: {len(violations)}건")

    print("\n" + "=" * 80 + "\n")


def output_json(analyzer, resolver, rule_checker):
    """JSON 형식 출력"""
    files_by_layer = analyzer.get_files_by_layer()
    summary = rule_checker.get_summary()
    import_count = resolver.get_import_count_by_layer()

    output = {
        "summary": summary,
        "statistics": {
            "files_by_layer": {
                layer: len(files) for layer, files in files_by_layer.items()
            },
            "import_count_by_layer": import_count,
        },
        "violations": rule_checker.violations,
        "dependency_matrix": resolver.get_layer_dependency_matrix(),
    }

    return json.dumps(output, indent=2, ensure_ascii=False)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="K-Beauty 백엔드 아키텍처 검증 도구"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="마크다운 보고서 생성 (ARCHITECTURE_VALIDATION_REPORT.md)",
    )
    parser.add_argument(
        "--diagram-level",
        choices=["1", "2", "3", "all", "none"],
        default="3",
        help="보고서에 포함할 다이어그램 수준 (기본: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="검증 결과를 JSON 형식으로 출력",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="생성된 보고서를 콘솔에 출력",
    )
    parser.add_argument(
        "--rules-file",
        default="rules/architecture_rules.json",
        help="규칙 파일 경로 (기본: rules/architecture_rules.json)",
    )
    parser.add_argument(
        "--src-path",
        default="src",
        help="소스 코드 경로 (기본: src)",
    )

    args = parser.parse_args()

    # 경로 확인
    if not Path(args.src_path).exists():
        print(f"❌ 소스 경로를 찾을 수 없습니다: {args.src_path}")
        sys.exit(1)

    # 규칙 로드
    rules = load_rules(args.rules_file)

    # 1. 코드 분석
    print(f"🔍 코드 분석 중... ({args.src_path})")
    analyzer = ASTAnalyzer(root_path=args.src_path)
    files_info = analyzer.analyze()
    print(f"✅ {len(files_info)}개 파일 분석 완료\n")

    # 2. 의존성 분석
    print("🔗 의존성 분석 중...")
    resolver = DependencyResolver(files_info, analyzer)
    resolver.build_dependency_graph()
    print(f"✅ 의존성 그래프 생성 완료\n")

    # 3. 규칙 검증
    print("📋 규칙 검증 중...")
    rule_checker = RuleChecker(rules, analyzer, resolver)
    violations = rule_checker.check_all()
    print(f"✅ 검증 완료: {len(violations)}개 위반 사항 감지\n")

    # 4. 다이어그램 생성
    diagram_generator = DiagramGenerator(files_info, analyzer, resolver)

    # 5. 보고서 생성
    if args.report:
        print(
            f"📝 보고서 생성 중 (다이어그램 Level: {args.diagram_level})..."
        )
        report_generator = ReportGenerator(
            analyzer, resolver, rule_checker, diagram_generator
        )
        report = report_generator.generate(
            diagram_level=args.diagram_level,
            output_file="docs/architecture/ARCHITECTURE_VALIDATION_REPORT.md",
            save_diagrams=True,
            diagrams_dir="docs/architecture",
        )

        print("✅ 보고서 생성 완료:")
        print("   📄 docs/architecture/ARCHITECTURE_VALIDATION_REPORT.md")
        if args.diagram_level != "none":
            print(f"   📊 docs/architecture/architecture_level*.md")
        print()

        if args.show:
            print(report)

    # 6. 콘솔 요약 출력
    print_console_summary(analyzer, resolver, rule_checker)

    # 7. JSON 출력
    if args.json:
        print("📊 JSON 형식 출력:\n")
        print(output_json(analyzer, resolver, rule_checker))

    # 종료 코드
    if violations and any(v.get("severity") == "error" for v in violations):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
