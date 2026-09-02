from typing import Any

from app.graph.state import MigrationState
from app.services.migration_plan_reviser import revise_plan
from app.services.migration_status import save_migration_status


async def revise_migration_plan(
    state: MigrationState,
) -> dict[str, Any]:
    """根据人工反馈修改迁移计划。"""

    task_id = state.get("task_id")
    source_code = state.get("source_code")
    source_analysis = state.get("source_analysis", {})
    previous_plan = state.get("migration_plan")
    feedback = (state.get("review_feedback") or "").strip()

    if not task_id:
        raise ValueError("task_id is required")

    if not source_code:
        raise ValueError("source_code is required")

    if not previous_plan:
        raise ValueError("migration_plan is required")

    if not feedback:
        raise ValueError("review_feedback is required")

    await save_migration_status(
        task_id=task_id,
        status="revising_plan",
        current_node="revise_plan",
    )

    revised_plan = await revise_plan(
        source_code=source_code,
        source_analysis=source_analysis,
        previous_plan=previous_plan,
        feedback=feedback,
    )

    return {
        "migration_plan": revised_plan.model_dump(mode="json"),
        "plan_revision_count": state.get("plan_revision_count", 0) + 1,
        "status": "revising_plan",
        "current_node": "revise_plan",
    }
