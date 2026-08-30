from app.graph.nodes.analyze_source import analyze_source
from app.graph.nodes.create_plan import create_plan
from app.graph.state import MigrationState
from langgraph.graph import END, START, StateGraph


async def create_migration_graph():
    """创建 React → Vue 迁移工作流。"""

    builder = StateGraph(MigrationState)

    builder.add_node("analyze_source", analyze_source)
    builder.add_node("create_plan", create_plan)

    builder.add_edge(START, "analyze_source")
    builder.add_edge("analyze_source", "create_plan")
    builder.add_edge("create_plan", END)

    return builder.compile()


async def run_migration_graph(
    task_id: int,
    filename: str,
    source_code: str,
) -> None:
    graph = await create_migration_graph()

    migration_data: MigrationState = {
        "task_id": task_id,
        "filename": filename,
        "source_code": source_code,
    }

    await graph.ainvoke(
        migration_data,
        config={
            "configurable": {
                "thread_id": task_id,
            }
        },
    )
