from typing import Any

from app.db.session import AsyncSessionLocal
from app.graph.state import MigrationState
from app.llm.code_repairer import (
    repair_vue_code,
)
from app.repositories.migration import update_migration_status

MAX_REPAIR_COUNT = 2


def normalize_plan(
    plan: Any,
) -> dict[str, Any]:
    """将迁移计划统一转换成字典。"""

    if plan is None:
        return {}

    if isinstance(plan, dict):
        return plan

    if hasattr(plan, "model_dump"):
        return plan.model_dump(mode="json")

    raise TypeError("approved_plan 必须是字典或 Pydantic 模型")


async def mark_task_repairing(
    task_id: int,
) -> None:
    """将数据库中的任务状态更新为 repairing。"""

    async with AsyncSessionLocal() as session, session.begin():
        await update_migration_status(
            session,
            task_id,
            status="repairing",
            current_node="repair_code",
        )


async def repair_code(
    state: MigrationState,
) -> dict[str, Any]:
    """根据验证错误修复 Vue 代码。"""

    task_id_value = state.get("task_id")
    generated_filename = state.get("generated_filename")
    generated_code = state.get("generated_code")
    validation_errors = state.get(
        "validation_errors",
        [],
    )
    repair_count = state.get(
        "repair_count",
        0,
    )

    if task_id_value is None:
        raise ValueError("task_id is required")

    if not generated_filename:
        raise ValueError("generated_filename is required")

    if not generated_code:
        raise ValueError("generated_code is required")

    if not validation_errors:
        raise ValueError("validation_errors is required")

    if repair_count >= MAX_REPAIR_COUNT:
        raise ValueError("已达到最大自动修复次数")

    # 系统运行错误不能交给大模型修复。
    runner_errors = [
        error for error in validation_errors if error.get("stage") == "runner"
    ]

    if runner_errors:
        raise ValueError("Node Runner 系统错误不能通过大模型修复")

    approved_plan = normalize_plan(
        state.get("approved_plan") or state.get("migration_plan")
    )

    task_id = int(task_id_value)

    # 前端可以通过轮询看到 repairing 状态。
    await mark_task_repairing(task_id)

    repaired_result = await repair_vue_code(
        generated_filename=generated_filename,
        generated_code=generated_code,
        validation_errors=validation_errors,
        approved_plan=approved_plan,
        repair_count=repair_count,
    )

    current_notes = state.get("generation_notes") or []

    repair_number = repair_count + 1

    new_notes = [
        *current_notes,
        (
            f"第 {repair_number} 次自动修复："
            + ("；".join(repaired_result.changes) or "已根据验证错误修复代码")
        ),
        *repaired_result.notes,
    ]

    return {
        # 使用修复后的代码覆盖旧代码。
        "generated_code": repaired_result.code,
        # 文件名保持不变。
        "generated_filename": generated_filename,
        # 记录修复说明。
        "generation_notes": new_notes,
        # 修复次数加一。
        "repair_count": repair_number,
        "status": "repaired",
        "current_node": "repair_code",
    }
