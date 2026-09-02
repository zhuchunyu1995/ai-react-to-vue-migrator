from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.migrations import Migration


async def create_migration(
    session: AsyncSession,
    *,
    filename: str,
    source_code: str,
) -> Migration:
    """创建迁移任务，但不负责提交事务。"""

    migration = Migration(
        filename=filename,
        source_code=source_code,
        status="queued",
    )

    session.add(migration)

    # 将 INSERT 发送到数据库，以便获取自增 ID
    await session.flush()
    await session.refresh(migration)

    return migration


async def get_migration_by_id(
    session: AsyncSession,
    task_id: int,
) -> Migration | None:
    """根据任务 ID 查询迁移任务。"""

    statement = select(Migration).where(Migration.id == task_id)
    result = await session.execute(statement)

    return result.scalar_one_or_none()


# 更新迁移任务状态
async def update_migration_status(
    session: AsyncSession,
    task_id: int,
    status: str,
    current_node: str,
) -> None:
    """更新迁移任务当前执行状态。"""

    await session.execute(
        update(Migration)
        .where(Migration.id == task_id)
        .values(
            status=status,
            current_node=current_node,
        )
    )


async def save_plan_for_review(
    task_id: int,
    migration_plan: dict,
) -> None:
    """保存迁移计划并更新任务为等待审核。"""

    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            update(Migration)
            .where(
                Migration.id == task_id,
                Migration.status.in_(
                    [
                        "planning",
                        "revising_plan",
                    ]
                ),
            )
            .values(
                migration_plan=migration_plan,
                status="waiting_for_review",
                current_node="human_review",
            )
        )


async def save_migration_review(
    session: AsyncSession,
    task_id: int,
    *,
    status: str,
    approved_plan: dict | None,
    review_feedback: str | None,
) -> None:
    """保存迁移计划的人工审核结果。"""

    await session.execute(
        update(Migration)
        .where(Migration.id == task_id)
        .values(
            status=status,
            current_node="human_review",
            approved_plan=approved_plan,
            review_feedback=review_feedback,
        )
    )


async def update_generated_code(
    session: AsyncSession,
    task_id: int,
    *,
    generated_filename: str,
    generated_code: str,
    generation_notes: list[str],
) -> None:
    """将大模型生成的 Vue 代码保存到迁移任务表。"""

    result = await session.execute(
        update(Migration)
        .where(Migration.id == task_id)
        .values(
            generated_filename=generated_filename,
            generated_code=generated_code,
            generation_notes=generation_notes,
            status="generated",
            current_node="persist_generated_code",
        )
    )

    # 防止任务已经被删除或 task_id 不存在
    if result.rowcount != 1:  # type: ignore
        raise ValueError(f"迁移任务不存在：{task_id}")


async def update_validation_result(
    session: AsyncSession,
    task_id: int,
    *,
    validation_passed: bool,
    validation_result: dict[str, Any],
    validation_errors: list[dict[str, Any]],
    status: str,
    current_node: str,
) -> Migration:
    """保存 Vue 代码验证结果。"""

    migration = await session.get(
        Migration,
        task_id,
    )

    if migration is None:
        raise ValueError(f"迁移任务不存在：{task_id}")

    migration.validation_passed = validation_passed

    migration.validation_result = validation_result

    migration.validation_errors = validation_errors

    migration.status = status
    migration.current_node = current_node

    # 将更新发送给数据库。
    # 这里不 commit，由外层 session.begin() 控制事务。
    await session.flush()

    return migration


async def update_migration_report(
    session: AsyncSession,
    task_id: int,
    *,
    migration_report: dict[str, Any],
    status: str,
    current_node: str,
) -> Migration:
    """保存迁移报告并更新任务状态。"""

    migration = await session.get(
        Migration,
        task_id,
    )

    if migration is None:
        raise ValueError(f"迁移任务不存在：{task_id}")

    migration.migration_report = migration_report

    migration.status = status
    migration.current_node = current_node

    # 只执行 flush，事务由外层统一提交。
    await session.flush()

    return migration
