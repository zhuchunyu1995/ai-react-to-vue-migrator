from app.graph.state import MigrationState
from app.integrations.node_runner import node_runner_client
from app.services.migration_status import save_migration_status


async def analyze_source(state: MigrationState) -> dict:
    """分析 React 源码。"""

    task_id = state.get("task_id")
    filename = state.get("filename")
    source_code = state.get("source_code")

    if not task_id:
        raise ValueError("task_id is required")

    if not filename:
        raise ValueError("filename is required")

    if not source_code:
        raise ValueError("source_code is required")

    # 告诉数据库：当前已经进入源码分析节点
    await save_migration_status(
        task_id=task_id,
        status="analyzing",
        current_node="analyze_source",
    )

    analysis = await node_runner_client.analyze(
        filename=filename,
        source_code=source_code,
    )

    return {
        "source_analysis": analysis.model_dump(mode="json"),
        "status": "analyzed",
        "current_node": "analyze_source",
    }
