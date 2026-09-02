from app.llm.client import get_llm
from app.llm.prompts import build_vue_generation_messages
from app.llm.schemas import VueCodeResult


async def generate_vue_code(
    *,
    source_code: str,
    source_analysis: dict,
    approved_plan: dict,
) -> VueCodeResult:
    """根据审核后的计划生成 Vue 代码。"""

    messages = build_vue_generation_messages(
        source_code=source_code,
        source_analysis=source_analysis,
        approved_plan=approved_plan,
    )

    structured_llm = get_llm().with_structured_output(
        VueCodeResult,
        method="function_calling",
    )

    result = await structured_llm.ainvoke(messages)

    return VueCodeResult.model_validate(result)
