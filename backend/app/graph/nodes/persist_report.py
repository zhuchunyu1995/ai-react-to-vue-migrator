from typing import Any

from app.db.session import AsyncSessionLocal
from app.graph.state import MigrationState
from app.repositories.migration import update_migration_report


async def persist_report(
    state: MigrationState,
) -> dict[str, Any]:
    """保存迁移报告并完成任务。"""

    task_id_value = state.get("task_id")
    migration_report = state.get("migration_report")

    if task_id_value is None:
        raise ValueError("task_id is required")

    if migration_report is None:
        raise ValueError("migration_report is required")

    task_id = int(task_id_value)

    # Graph 后台任务使用独立数据库会话。
    async with AsyncSessionLocal() as session, session.begin():
        await update_migration_report(
            session,
            task_id,
            migration_report=migration_report,
            status="completed",
            current_node="completed",
        )

    return {
        "status": "completed",
        "current_node": "completed",
    }
