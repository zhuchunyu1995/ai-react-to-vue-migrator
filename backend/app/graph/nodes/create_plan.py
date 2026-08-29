from app.graph.state import MigrationState


def create_plan(state: MigrationState) -> dict:
    """创建迁移计划。Day 3 接入 LLM Structured Output。"""

    return {
        "migration_plan": {
            "summary": "迁移计划待生成",
        },
        "status": "plan_created",
        "current_node": "create_plan",
    }
