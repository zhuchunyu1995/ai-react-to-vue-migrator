from typing import Any

from app.domain.migration_rules import build_rule_suggestions
from app.llm.client import get_llm
from app.llm.prompts import build_migration_plan_messages
from app.llm.schemas import MigrationPlan
from app.services.migration_plan_validator import (
    validate_migration_plan,
)


# 迁移计划业务服务
async def create_plan(
    source_code: str,
    source_analysis: dict[str, Any],
    target: dict[str, str],
) -> MigrationPlan:
    """组合规则建议和大模型，生成结构化迁移计划。"""

    # 先根据 AST 分析结果生成确定性规则建议
    rule_suggestions = build_rule_suggestions(
        source_analysis=source_analysis,
    )

    # 构建发送给大模型的消息
    messages = build_migration_plan_messages(
        source_code=source_code,
        source_analysis=source_analysis,
        rule_suggestions=rule_suggestions,
        target=target,
    )

    # 获取大模型客户端
    llm = get_llm()

    # 强制大模型按照 MigrationPlan 结构返回
    structured_llm = llm.with_structured_output(
        MigrationPlan,
        # 使用 Tool Calling 约束结构，
        # 避免发送 DeepSeek 不支持的 json_schema response_format
        method="function_calling",
    )
    # 异步生成迁移计划
    migration_plan = await structured_llm.ainvoke(messages)
    migration_plan = MigrationPlan.model_validate(migration_plan)

    # 校验迁移计划是否符合规则
    validation_errors = validate_migration_plan(
        plan=migration_plan,
        source_analysis=source_analysis,
    )

    if validation_errors:
        raise ValueError("迁移计划校验失败：" + "；".join(validation_errors))

    return migration_plan
