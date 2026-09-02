from typing import Any

from app.db.session import AsyncSessionLocal
from app.graph.state import MigrationState
from app.repositories.migration import (
    update_migration_status,
    update_validation_result,
)
from app.services.node_runner import (
    NodeRunnerError,
    validate_vue_code,
)

MAX_REPAIR_COUNT = 2


async def persist_status(
    task_id: int,
    *,
    status: str,
    current_node: str,
) -> None:
    """使用独立数据库会话保存状态。"""

    async with AsyncSessionLocal() as session, session.begin():
        await update_migration_status(
            session,
            task_id,
            status=status,
            current_node=current_node,
        )


async def persist_validation_result(
    task_id: int,
    *,
    validation_passed: bool,
    validation_result: dict[str, Any],
    validation_errors: list[dict[str, Any]],
    status: str,
) -> None:
    """使用独立数据库会话保存验证结果。"""

    async with AsyncSessionLocal() as session, session.begin():
        await update_validation_result(
            session,
            task_id,
            validation_passed=validation_passed,
            validation_result=validation_result,
            validation_errors=validation_errors,
            status=status,
            current_node="validate_code",
        )


async def validate_code(
    state: MigrationState,
) -> dict[str, Any]:
    """验证生成的 Vue 代码。"""

    task_id_value = state.get("task_id")
    generated_filename = state.get("generated_filename")
    generated_code = state.get("generated_code")

    if task_id_value is None:
        raise ValueError("task_id is required")

    if not generated_filename:
        raise ValueError("generated_filename is required")

    if not generated_code:
        raise ValueError("generated_code is required")

    task_id = int(task_id_value)

    # 告诉前端当前已经进入验证阶段。
    await persist_status(
        task_id,
        status="validating",
        current_node="validate_code",
    )

    try:
        result = await validate_vue_code(
            filename=generated_filename,
            source_code=generated_code,
        )
    except NodeRunnerError as exc:
        # Node Runner 本身启动失败、超时或者返回非法 JSON。
        # 这种错误不应该交给大模型修复代码。
        runner_error = {
            "stage": "runner",
            "message": str(exc),
            "line": None,
            "column": None,
        }

        validation_result = {
            "success": False,
            "checks": {},
            "errors": [runner_error],
        }

        await persist_validation_result(
            task_id,
            validation_passed=False,
            validation_result=validation_result,
            validation_errors=[runner_error],
            status="failed",
        )

        return {
            "validation_passed": False,
            "validation_checks": {},
            "validation_errors": [runner_error],
            "validation_result": validation_result,
            "status": "failed",
            "current_node": "validate_code",
        }

    validation_result = result.model_dump(mode="json")

    validation_errors = [error.model_dump(mode="json") for error in result.errors]

    repair_count = state.get(
        "repair_count",
        0,
    )

    if result.success:
        status = "validated"
    elif repair_count >= MAX_REPAIR_COUNT:
        status = "failed"
    else:
        status = "validation_failed"

    await persist_validation_result(
        task_id,
        validation_passed=result.success,
        validation_result=validation_result,
        validation_errors=validation_errors,
        status=status,
    )

    return {
        "validation_passed": result.success,
        "validation_checks": result.checks,
        "validation_errors": validation_errors,
        "validation_result": validation_result,
        "status": status,
        "current_node": "validate_code",
    }
