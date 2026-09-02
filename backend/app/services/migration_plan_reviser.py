from typing import Any

from app.domain.migration_rules import build_rule_suggestions
from app.llm.client import get_llm
from app.llm.revision_prompts import build_plan_revision_messages
from app.llm.schemas import MigrationPlan
from app.services.migration_plan_validator import validate_migration_plan


async def revise_plan(
    *,
    source_code: str,
    source_analysis: dict[str, Any],
    previous_plan: dict[str, Any],
    feedback: str,
) -> MigrationPlan:
    """根据用户反馈重新生成迁移计划。"""

    target = {
        "framework": "vue3",
        "language": "typescript",
        "component_style": "script_setup",
    }

    rule_suggestions = build_rule_suggestions(source_analysis)

    messages = build_plan_revision_messages(
        source_code=source_code,
        source_analysis=source_analysis,
        previous_plan=previous_plan,
        feedback=feedback,
        rule_suggestions=rule_suggestions,
        target=target,
    )

    structured_llm = get_llm().with_structured_output(
        MigrationPlan,
        method="function_calling",
    )

    result = await structured_llm.ainvoke(messages)
    revised_plan = MigrationPlan.model_validate(result)

    validation_errors = validate_migration_plan(
        plan=revised_plan,
        source_analysis=source_analysis,
    )

    if validation_errors:
        raise ValueError("修改后的迁移计划校验失败：" + "；".join(validation_errors))

    return revised_plan
