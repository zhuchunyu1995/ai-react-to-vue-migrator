from app.graph.state import MigrationState
from app.services.migration_status import save_migration_status


async def create_plan(state: MigrationState) -> dict:
    """调用大模型生成迁移计划。"""

    task_id = state.get("task_id")
    source_code = state.get("source_code")
    if not task_id:
        raise ValueError("task_id is required")
    if not source_code:
        raise ValueError("source_code is required")

    # 前端下一次轮询时就会看到 planning
    await save_migration_status(
        task_id=task_id,
        status="planning",
        current_node="create_plan",
    )

    # migration_plan = await generate_migration_plan(
    #     source_code=state["source_code"],
    #     source_analysis=state["source_analysis"],
    # )

    # 当计划生成完成、准备等待人工确认时，再写入：
    # await save_migration_status(
    #     task_id=task_id,
    #     status="waiting_for_review",
    #     current_node="human_review",
    # )

    return {
        # "migration_plan": migration_plan,
        "status": "planned",
        "current_node": "create_plan",
    }
