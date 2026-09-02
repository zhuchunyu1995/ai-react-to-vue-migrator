from typing import Any

from app.llm.schemas import MigrationPlan

CORE_DEPENDENCIES = {
    "vue",
    "react",
    "typescript",
}


def validate_migration_plan(
    plan: MigrationPlan,
    source_analysis: dict[str, Any],
) -> list[str]:
    """检查迁移计划是否存在明显语义错误。"""

    errors: list[str] = []

    target_text = "\n".join(mapping.target for mapping in plan.mappings)

    for prop_name in source_analysis.get("props", []):
        invalid_ref_access = f"{prop_name}.value"

        if invalid_ref_access in target_text:
            errors.append(
                f"Prop {prop_name} 不是 ref，"
                f"禁止使用 {invalid_ref_access}，"
                f"应该使用 props.{prop_name}"
            )

    has_v_model = "v-model" in target_text
    has_input_event = "@input" in target_text
    has_change_event = "@change" in target_text

    if has_v_model and (has_input_event or has_change_event):
        errors.append("输入框已经使用 v-model，不能同时生成 @input 或 @change")

    # Vue、React、TypeScript 不应该作为额外依赖
    for dependency in plan.dependencies:
        dependency_name = dependency.split("@")[0].lower()

        if dependency_name in CORE_DEPENDENCIES:
            errors.append(f"dependencies 不应该包含基础依赖：{dependency}")

    # 迁移计划必须包含至少一条映射
    if not plan.mappings:
        errors.append("迁移计划 mappings 不能为空")

    return errors
