import logging
from typing import Literal

from app.graph.nodes.analyze_source import analyze_source
from app.graph.nodes.create_plan import create_plan
from app.graph.nodes.generate_code import generate_code
from app.graph.nodes.generate_report import generate_report
from app.graph.nodes.human_review import human_review
from app.graph.nodes.persist_generated_code import persist_generated_code
from app.graph.nodes.persist_report import persist_report
from app.graph.nodes.repair_code import (
    MAX_REPAIR_COUNT,
    repair_code,
)
from app.graph.nodes.revise_plan import revise_migration_plan
from app.graph.nodes.validate_code import (
    validate_code,
)
from app.graph.state import MigrationState
from app.services.migration_status import save_migration_status
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

logger = logging.getLogger(__name__)


def route_after_validation_now(
    state: MigrationState,
) -> Literal["passed", "failed"]:
    if state.get("validation_passed"):
        return "passed"

    return "failed"


def route_after_validation(
    state: MigrationState,
) -> Literal[
    "passed",
    "repair",
    "failed",
]:
    """根据验证结果决定下一步。"""

    if state.get("validation_passed"):
        return "passed"

    validation_errors = state.get(
        "validation_errors",
        [],
    )

    # 环境错误不调用大模型修复。
    has_runner_error = any(
        error.get("stage") == "runner" for error in validation_errors
    )

    if has_runner_error:
        return "failed"

    repair_count = state.get(
        "repair_count",
        0,
    )

    if repair_count < MAX_REPAIR_COUNT:
        return "repair"

    return "failed"


def create_migration_graph(
    checkpointer: BaseCheckpointSaver,
) -> CompiledStateGraph:
    """创建 React → Vue 迁移工作流。"""

    builder = StateGraph(MigrationState)

    builder.add_node("analyze_source", analyze_source)
    builder.add_node("create_plan", create_plan)
    builder.add_node("human_review", human_review)
    builder.add_node("generate_code", generate_code)
    builder.add_node("persist_generated_code", persist_generated_code)
    builder.add_node("validate_code", validate_code)
    builder.add_node("generate_report", generate_report)
    builder.add_node("persist_report", persist_report)
    builder.add_node("repair_code", repair_code)
    builder.add_node("revise_plan", revise_migration_plan)

    builder.add_edge(START, "analyze_source")
    builder.add_edge("analyze_source", "create_plan")
    builder.add_edge("create_plan", "human_review")
    builder.add_edge("revise_plan", "human_review")
    builder.add_edge("generate_code", "persist_generated_code")
    builder.add_edge(
        "persist_generated_code",
        "validate_code",
    )

    builder.add_conditional_edges(
        "validate_code",
        route_after_validation,
        {
            "passed": "generate_report",
            "repair": "repair_code",
            "failed": END,
        },
    )

    builder.add_edge(
        "generate_report",
        "persist_report",
    )
    builder.add_edge(
        "repair_code",
        "persist_generated_code",
    )
    builder.add_edge(
        "persist_report",
        END,
    )
    return builder.compile(checkpointer=checkpointer)


async def run_migration_graph(
    graph: CompiledStateGraph,
    task_id: int,
    filename: str,
    source_code: str,
) -> None:
    migration_data: MigrationState = {
        "task_id": task_id,
        "filename": filename,
        "source_code": source_code,
        "repair_count": 0,
        "plan_revision_count": 0,
    }

    try:
        await graph.ainvoke(
            migration_data,
            config={
                "configurable": {
                    "thread_id": str(task_id),
                }
            },
        )
    except Exception:
        logger.exception(
            "执行迁移工作流失败，task_id=%s",
            task_id,
        )

        await save_migration_status(
            task_id=task_id,
            status="failed",
            current_node="workflow_error",
        )


async def resume_migration_graph(
    graph: CompiledStateGraph,
    task_id: int,
    *,
    action: str,
    migration_plan: dict | None,
    feedback: str | None,
) -> None:
    try:
        await graph.ainvoke(
            Command(
                resume={
                    "action": action,
                    "migration_plan": migration_plan,
                    "feedback": feedback,
                }
            ),
            config={
                "configurable": {
                    "thread_id": str(task_id),
                }
            },
        )
    except Exception:
        logger.exception(
            "恢复迁移工作流失败，task_id=%s",
            task_id,
        )

        await save_migration_status(
            task_id=task_id,
            status="failed",
            current_node="workflow_error",
        )
