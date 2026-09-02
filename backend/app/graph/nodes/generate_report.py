from datetime import UTC, datetime
from typing import Any

from app.graph.state import MigrationState


def build_report_markdown(
    report: dict[str, Any],
) -> str:
    """将结构化迁移报告转换成 Markdown。"""

    summary = report["summary"]
    mappings = report["mappings"]
    validation = report["validation"]
    risks = report["risks"]
    manual_checks = report["manual_checks"]
    generation_notes = report["generation_notes"]

    lines: list[str] = [
        "# React → Vue 迁移报告",
        "",
        "## 基本信息",
        "",
        f"- 组件名称：{summary['component_name']}",
        f"- React 文件：{summary['source_filename']}",
        f"- Vue 文件：{summary['generated_filename']}",
        f"- 迁移结果：{summary['result']}",
        f"- AI 修复次数：{summary['repair_count']}",
        "",
        "## 迁移映射",
        "",
    ]

    if mappings:
        for mapping in mappings:
            source = mapping.get(
                "source",
                "未知",
            )

            target = mapping.get(
                "target",
                "未知",
            )

            category = mapping.get(
                "category",
                "other",
            )

            reason = mapping.get(
                "reason",
                "",
            )

            lines.append(f"- **{category}**：`{source}` → `{target}`")

            if reason:
                lines.append(f"  - 原因：{reason}")
    else:
        lines.append("- 没有迁移映射记录")

    lines.extend(
        [
            "",
            "## 自动验证",
            "",
        ]
    )

    checks = validation.get(
        "checks",
        {},
    )

    for check_name, passed in checks.items():
        result_text = "通过" if passed else "失败"

        lines.append(f"- {check_name}：{result_text}")

    validation_errors = validation.get(
        "errors",
        [],
    )

    if validation_errors:
        lines.extend(
            [
                "",
                "### 验证错误",
                "",
            ]
        )

        for error in validation_errors:
            stage = error.get(
                "stage",
                "unknown",
            )

            message = error.get(
                "message",
                "未知错误",
            )

            line = error.get("line")
            column = error.get("column")

            position = ""

            if line is not None:
                position = f"（第 {line} 行"

                if column is not None:
                    position += f"，第 {column} 列"

                position += "）"

            lines.append(f"- [{stage}] {message}{position}")

    lines.extend(
        [
            "",
            "## 风险提示",
            "",
        ]
    )

    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- 暂无已知风险")

    lines.extend(
        [
            "",
            "## 人工检查项",
            "",
        ]
    )

    if manual_checks:
        for item in manual_checks:
            lines.append(f"- [ ] {item}")
    else:
        lines.append("- 无额外人工检查项")

    lines.extend(
        [
            "",
            "## 代码生成说明",
            "",
        ]
    )

    if generation_notes:
        for note in generation_notes:
            lines.append(f"- {note}")
    else:
        lines.append("- 无额外生成说明")

    return "\n".join(lines)


async def generate_report(
    state: MigrationState,
) -> dict[str, Any]:
    """根据工作流现有数据生成迁移报告。"""

    if not state.get("validation_passed"):
        raise ValueError("代码验证未通过，不能生成迁移报告")

    source_analysis = state.get(
        "source_analysis",
        {},
    )

    approved_plan = state.get("approved_plan") or state.get("migration_plan") or {}

    validation_result = state.get(
        "validation_result",
        {},
    )

    source_filename = state.get(
        "filename",
        "unknown.tsx",
    )

    generated_filename = state.get(
        "generated_filename",
        "GeneratedComponent.vue",
    )

    component_name = (
        approved_plan.get("component_name")
        or source_analysis.get("component_name")
        or generated_filename.removesuffix(".vue")
    )

    mappings = approved_plan.get(
        "mappings",
        [],
    )

    risks = approved_plan.get(
        "risks",
        [],
    )

    manual_checks = approved_plan.get(
        "manual_checks",
        [],
    )

    generation_notes = state.get(
        "generation_notes",
        [],
    )

    repair_count = state.get(
        "repair_count",
        0,
    )

    rule_mapping_count = sum(
        1 for mapping in mappings if mapping.get("strategy") == "rule"
    )

    llm_mapping_count = sum(
        1 for mapping in mappings if mapping.get("strategy") == "llm"
    )

    review_mapping_count = sum(1 for mapping in mappings if mapping.get("needs_review"))

    report: dict[str, Any] = {
        "version": "1.0",
        # JSON 中保存字符串时间，避免序列化问题。
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "component_name": component_name,
            "source_filename": source_filename,
            "generated_filename": generated_filename,
            "result": "success",
            "repair_count": repair_count,
        },
        "statistics": {
            "mapping_count": len(mappings),
            "rule_mapping_count": (rule_mapping_count),
            "llm_mapping_count": (llm_mapping_count),
            "needs_review_count": (review_mapping_count),
        },
        "mappings": mappings,
        "validation": {
            "passed": validation_result.get(
                "success",
                False,
            ),
            "checks": validation_result.get(
                "checks",
                {},
            ),
            "errors": validation_result.get(
                "errors",
                [],
            ),
            "details": validation_result.get(
                "details",
                {},
            ),
        },
        "risks": risks,
        "manual_checks": manual_checks,
        "generation_notes": generation_notes,
    }

    # 同时生成一份可以直接展示或下载的 Markdown。
    report["markdown"] = build_report_markdown(report)

    return {
        "migration_report": report,
        "status": "report_generated",
        "current_node": "generate_report",
    }
