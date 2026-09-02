from app.graph.state import MigrationState
from app.llm.client import get_llm
from app.llm.prompts import (
    build_migration_plan_repair_messages,
)
from app.llm.schemas import MigrationPlan
from app.services import migration_planner
from app.services.migration_plan_validator import validate_migration_plan
from app.services.migration_status import save_migration_status


async def create_plan(state: MigrationState) -> dict:
    """调用大模型生成迁移计划。"""

    task_id = state.get("task_id")
    source_code = state.get("source_code")
    source_analysis = state.get("source_analysis")
    if not task_id:
        raise ValueError("task_id is required")
    if not source_code:
        raise ValueError("source_code is required")

    await save_migration_status(
        task_id=task_id,
        status="planning",
        current_node="create_plan",
    )

    target = {
        "framework": "vue3",
        "language": "typescript",
        "component_style": "script_setup",
    }

    # 调用大模型生成迁移计划
    migration_plan = await migration_planner.create_plan(
        source_code=source_code,
        source_analysis=source_analysis or {},
        target=target,
    )

    migration_plan = MigrationPlan.model_validate(migration_plan)
    # 第一次业务规则校验
    validation_errors = validate_migration_plan(
        plan=migration_plan,
        source_analysis=source_analysis or {},
    )

    # 第一次就通过，直接返回
    if not validation_errors:
        return {
            "migration_plan": migration_plan.model_dump(mode="json"),
            "status": "planned",
            "current_node": "create_plan",
        }

    # 将错误、原计划和原始上下文重新交给大模型
    repair_messages = build_migration_plan_repair_messages(
        source_code=source_code,
        source_analysis=source_analysis or {},
        rule_suggestions=state.get("rule_suggestions", []),
        target=target,
        invalid_plan=migration_plan.model_dump(mode="json"),
        validation_errors=validation_errors,
    )

    structured_llm = get_llm().with_structured_output(
        MigrationPlan,
        # 使用 Tool Calling 约束结构，
        # 避免发送 DeepSeek 不支持的 json_schema response_format
        method="function_calling",
    )

    # 只自动修复一次
    repaired_plan = await structured_llm.ainvoke(repair_messages)

    repaired_plan = MigrationPlan.model_validate(repaired_plan)

    # 对修复后的计划再次校验
    remaining_errors = validate_migration_plan(
        plan=repaired_plan,
        source_analysis=source_analysis or {},
    )

    # 第二次仍然失败，不再继续消耗 Token
    if remaining_errors:
        raise ValueError(
            "迁移计划自动修复后仍未通过校验：" + "；".join(remaining_errors)
        )

    return {
        "migration_plan": repaired_plan.model_dump(mode="json"),
        "status": "planned",
        "current_node": "create_plan",
    }
