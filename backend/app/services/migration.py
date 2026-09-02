from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migrations import Migration
from app.repositories.migration import (
    create_migration,
    get_migration_by_id,
    save_migration_review,
)
from app.schemas.migration import (
    MigrationCreateRequest,
    MigrationDetailResponse,
    MigrationReviewRequest,
)


async def create_migration_task(
    session: AsyncSession,
    payload: MigrationCreateRequest,
) -> Migration:
    """创建任务并控制事务。"""

    async with session.begin():
        migration = await create_migration(
            session,
            filename=payload.filename,
            source_code=payload.source_code,
        )
    return migration


async def get_migration_task(
    session: AsyncSession,
    task_id: int,
) -> MigrationDetailResponse:
    """根据任务ID获取迁移任务。"""

    migration = await get_migration_by_id(
        session,
        task_id=task_id,
    )
    if migration is None:
        raise HTTPException(status_code=404, detail="迁移任务不存在")

    return MigrationDetailResponse.model_validate(migration)


async def review_migration(
    session: AsyncSession,
    task_id: int,
    payload: MigrationReviewRequest,
) -> MigrationDetailResponse:
    """校验并保存人工审核结果，事务提交后再由路由恢复工作流。"""

    migration = await get_migration_by_id(session, task_id)
    if migration is None:
        raise HTTPException(status_code=404, detail="迁移任务不存在")

    if migration.status != "waiting_for_review":
        raise HTTPException(
            status_code=409,
            detail=f"当前任务状态为 {migration.status}，不能重复审核",
        )

    approved_plan = None
    review_feedback = None

    if payload.action == "approve":
        assert payload.migration_plan is not None

        approved_plan = payload.migration_plan.model_dump(mode="json")
        status = "approved"

    elif payload.action == "request_changes":
        review_feedback = (payload.feedback or "").strip()
        status = "revision_requested"

    else:
        status = "cancelled"

    await save_migration_review(
        session,
        task_id,
        status=status,
        approved_plan=approved_plan,
        review_feedback=review_feedback,
    )

    # 必须在恢复 LangGraph 前提交，后续节点才能读取到最终审核结果
    await session.commit()

    updated_migration = await get_migration_by_id(session, task_id)

    if updated_migration is None:
        raise HTTPException(
            status_code=404, detail=f"Migration with id {task_id} not found"
        )
    return MigrationDetailResponse.model_validate(updated_migration)
