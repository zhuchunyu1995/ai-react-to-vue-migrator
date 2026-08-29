from app.graph.state import MigrationState


def analyze_source(state: MigrationState) -> dict:
    """分析 React 源码。Day 2 接入 Node Runner。"""

    if "filename" not in state:
        raise ValueError("filename is required")

    return {
        "source_analysis": {
            "filename": state["filename"],
        },
        "status": "analyzed",
        "current_node": "analyze_source",
    }
