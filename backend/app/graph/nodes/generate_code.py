from app.graph.state import MigrationState
from app.services.migration_status import save_migration_status
from app.services.vue_generator import generate_vue_code


async def generate_code(state: MigrationState) -> dict:
    """根据人工确认后的迁移计划生成 Vue 组件。"""

    task_id = state.get("task_id")
    source_code = state.get("source_code")
    source_analysis = state.get("source_analysis")
    approved_plan = state.get("approved_plan")

    if not task_id:
        raise ValueError("task_id is required")

    if not source_code:
        raise ValueError("source_code is required")

    if not approved_plan:
        raise ValueError("approved_plan is required")

    await save_migration_status(
        task_id=task_id,
        status="generating",
        current_node="generate_code",
    )

    result = await generate_vue_code(
        source_code=source_code,
        source_analysis=source_analysis or {},
        approved_plan=approved_plan,
    )

    return {
        "generated_filename": result.filename,
        "generated_code": result.code,
        "generation_notes": result.notes,
        "status": "generated",
        "current_node": "generate_code",
    }
