from graph.nodes.analyze_source import analyze_source
from graph.nodes.create_plan import create_plan
from graph.state import MigrationState
from langgraph.graph import END, START, StateGraph


def create_migration_graph():
    """创建 React → Vue 迁移工作流。"""

    builder = StateGraph(MigrationState)

    builder.add_node("analyze_source", analyze_source)
    builder.add_node("create_plan", create_plan)

    builder.add_edge(START, "analyze_source")
    builder.add_edge("analyze_source", "create_plan")
    builder.add_edge("create_plan", END)

    return builder.compile()
