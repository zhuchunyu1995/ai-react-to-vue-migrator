from typing import Any

"""
1.0：完全可靠，一定能正确转换
0.8 ~ 0.99：高度可靠，但存在边缘情况
0.5 ~ 0.79：中等可靠，可能需要验证
0.0 ~ 0.49：低可靠，建议人工审查
"""
MIGRATION_RULES: dict[str, dict[str, Any]] = {
    "useState": {
        "target": "ref",
        "reason": "React 局部状态映射为 Vue 响应式引用",
        "confidence": 1.0,
        "needs_review": False,
    },
    "useMemo": {
        "target": "computed",
        "reason": "缓存计算结果映射为 Vue 计算属性",
        "confidence": 0.95,
        "needs_review": False,
    },
    "useRef": {
        "target": "ref",
        "reason": "React 引用映射为 Vue ref",
        "confidence": 0.9,
        "needs_review": False,
    },
}


def build_rule_suggestions(
    source_analysis: dict,
) -> list[dict]:
    """根据 AST 分析结果生成确定性迁移建议。"""

    suggestions: list[dict] = []

    for hook in source_analysis.get("hooks", []):
        hook_name = hook["name"]
        rule = MIGRATION_RULES.get(hook_name)

        if not rule:
            continue

        suggestions.append(
            {
                "source": hook_name,
                "target": rule["target"],
                "reason": rule["reason"],
                "confidence": rule["confidence"],
                "needs_review": rule["needs_review"],
                "source_line": hook.get("line"),
            }
        )

    return suggestions
