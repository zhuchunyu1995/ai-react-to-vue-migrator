from typing import Any

from app.graph.state import MigrationState
from app.services.node_runner import (
    analyze_react_source,
)


async def analyze_source(
    state: MigrationState,
) -> dict[str, Any]:
    """分析 React 源代码。"""

    task_id = state.get("task_id")
    filename = state.get("filename")
    source_code = state.get("source_code")

    if task_id is None:
        raise ValueError("task_id is required")

    if not filename:
        raise ValueError("filename is required")

    if not source_code:
        raise ValueError("source_code is required")

    # Python 调用 Node Runner。
    source_analysis = await analyze_react_source(
        filename=filename,
        source_code=source_code,
    )

    return {
        "source_analysis": source_analysis,
        "status": "analyzed",
        "current_node": "analyze_source",
    }
