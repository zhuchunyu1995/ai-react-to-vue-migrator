from typing import Any

from app.llm.client import get_llm
from app.llm.prompts import (
    build_repair_code_messages,
)
from app.llm.schemas import RepairCodeResult
from pydantic import BaseModel


def remove_markdown_fence(
    code: str,
) -> str:
    """移除大模型可能返回的 Markdown 代码围栏。"""

    stripped_code = code.strip()

    if not stripped_code.startswith("```"):
        return stripped_code

    lines = stripped_code.splitlines()

    # 删除第一行，例如 ```vue。
    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    # 删除最后一行 ```。
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


async def repair_vue_code(
    *,
    generated_filename: str,
    generated_code: str,
    validation_errors: list[dict[str, Any]],
    approved_plan: dict[str, Any],
    repair_count: int,
) -> RepairCodeResult:
    """调用大模型修复 Vue 代码。"""

    messages = build_repair_code_messages(
        generated_filename=generated_filename,
        generated_code=generated_code,
        validation_errors=validation_errors,
        approved_plan=approved_plan,
        repair_count=repair_count,
    )

    llm = get_llm()

    # 强制大模型按照 RepairCodeResult 返回。
    structured_llm = llm.with_structured_output(
        RepairCodeResult, method="function_calling"
    )

    raw_result = await structured_llm.ainvoke(messages)

    # 将 BaseModel、dict 等返回类型统一转换。
    if isinstance(raw_result, BaseModel):
        result_data = raw_result.model_dump(mode="json")
    else:
        result_data = raw_result

    # 明确声明变量类型。
    result: RepairCodeResult = RepairCodeResult.model_validate(result_data)

    cleaned_code = remove_markdown_fence(result.code)

    if not cleaned_code:
        raise ValueError("大模型返回的修复代码为空")

    return RepairCodeResult(
        code=cleaned_code,
        changes=result.changes,
        notes=result.notes,
    )
