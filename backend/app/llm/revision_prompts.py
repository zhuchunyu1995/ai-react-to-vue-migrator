from typing import Any

from app.llm.prompts import CREATE_PLAN_SYSTEM_PROMPT, format_json
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


def build_plan_revision_messages(
    *,
    source_code: str,
    source_analysis: dict[str, Any],
    previous_plan: dict[str, Any],
    feedback: str,
    rule_suggestions: list[dict[str, Any]],
    target: dict[str, str],
) -> list[BaseMessage]:
    """根据用户反馈重新生成完整迁移计划。"""

    human_prompt = f"""
请根据用户反馈修改上一版 React → Vue 3 迁移计划。

## 用户反馈

{feedback}

## 上一版迁移计划

{format_json(previous_plan)}

## AST 分析结果

{format_json(source_analysis)}

## 确定性规则建议

{format_json(rule_suggestions)}

## 目标配置

{format_json(target)}

## React 原始源码

<react_source>
{source_code}
</react_source>

## 修改要求

1. 必须处理用户反馈。
2. 保留上一版中正确的内容。
3. 返回完整 MigrationPlan，不能只返回修改部分。
4. 不允许修改与反馈无关的业务语义。
5. 不生成 Vue SFC，只生成迁移计划。
6. mappings 与 generation_constraints 必须一致。
""".strip()

    return [
        SystemMessage(content=CREATE_PLAN_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]
