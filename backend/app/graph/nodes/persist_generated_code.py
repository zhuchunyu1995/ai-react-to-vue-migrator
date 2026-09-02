from app.graph.state import MigrationState
from app.services.migration_artifact import save_generated_result


async def persist_generated_code(
    state: MigrationState,
) -> dict:
    """将 LangGraph State 中的 Vue 代码保存到业务数据库。"""

    task_id = state.get("task_id")
    generated_filename = state.get("generated_filename")
    generated_code = state.get("generated_code")
    generation_notes = state.get("generation_notes", [])

    if task_id is None:
        raise ValueError("task_id is required")

    if not generated_filename:
        raise ValueError("generated_filename is required")

    if not generated_code:
        raise ValueError("generated_code is required")

    await save_generated_result(
        task_id=task_id,
        generated_filename=generated_filename,
        generated_code=generated_code,
        generation_notes=generation_notes,
    )

    # generated_code 已经存在于 LangGraph State，
    # 这里不需要重复返回完整代码。
    return {
        "status": "generated",
        "current_node": "persist_generated_code",
    }
