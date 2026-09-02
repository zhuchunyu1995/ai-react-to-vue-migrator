from typing import Literal, cast

from app.graph.state import MigrationState
from app.repositories.migration import save_plan_for_review
from langgraph.graph import END
from langgraph.types import Command, interrupt

ReviewDestination = Literal[
    "generate_code",
    "revise_plan",
    "__end__",
]


async def human_review(
    state: MigrationState,
) -> Command[ReviewDestination]:
    """保存迁移计划、暂停工作流，并根据审核结果跳转。"""

    task_id = state.get("task_id")
    migration_plan = state.get("migration_plan")

    if not task_id:
        raise ValueError("task_id is required")

    if not migration_plan:
        raise ValueError("migration_plan is required")

    await save_plan_for_review(
        task_id=task_id,
        migration_plan=migration_plan,
    )

    review_result = interrupt(
        {
            "task_id": task_id,
            "migration_plan": migration_plan,
            "revision_count": state.get("plan_revision_count", 0),
            "message": "请审核迁移计划",
        }
    )

    action = review_result.get("action")

    if action == "approve":
        return Command(
            update={
                "approved_plan": (
                    review_result.get("migration_plan") or migration_plan
                ),
                "review_decision": "approve",
                "status": "approved",
                "current_node": "human_review",
            },
            goto="generate_code",
        )

    if action == "request_changes":
        feedback = (review_result.get("feedback") or "").strip()

        if not feedback:
            raise ValueError("要求修改计划时 feedback 不能为空")

        return Command(
            update={
                "review_decision": "request_changes",
                "review_feedback": feedback,
                "status": "revision_requested",
                "current_node": "human_review",
            },
            goto="revise_plan",
        )

    return Command[ReviewDestination](
        update={
            "review_decision": "cancel",
            "status": "cancelled",
            "current_node": "human_review",
        },
        goto=cast(ReviewDestination, END),
    )
