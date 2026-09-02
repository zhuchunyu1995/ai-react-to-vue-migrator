from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.graph.builder import resume_migration_graph, run_migration_graph
from app.schemas.migration import (
    MigrationCreateRequest,
    MigrationDetailResponse,
    MigrationReviewRequest,
)
from app.services import migration

router = APIRouter(prefix="/api/migrations", tags=["migrations"])


# 获取迁移任务详情
@router.get("/{task_id}", response_model=MigrationDetailResponse)
async def get_migration_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: int = Path(..., description="迁移任务ID"),
):
    return await migration.get_migration_task(db, task_id=task_id)


# 创建迁移任务
@router.post("/", status_code=202)
async def create_migration_route(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: MigrationCreateRequest,
    background_tasks: BackgroundTasks,
):
    response = await migration.create_migration_task(
        db,
        payload=payload,
    )
    background_tasks.add_task(
        run_migration_graph,
        request.app.state.migration_graph,
        response.id,
        payload.filename,
        payload.source_code,
    )

    return response


# 迁移任务审核
@router.post(
    "/{task_id}/review",
    status_code=202,
    response_model=MigrationDetailResponse,
)
async def review_migration_route(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    payload: MigrationReviewRequest,
    task_id: int = Path(..., description="迁移任务ID"),
):
    response = await migration.review_migration(
        db,
        task_id=task_id,
        payload=payload,
    )

    background_tasks.add_task(
        resume_migration_graph,
        request.app.state.migration_graph,
        task_id,
        action=payload.action,
        migration_plan=(
            payload.migration_plan.model_dump(mode="json")
            if payload.migration_plan
            else None
        ),
        feedback=payload.feedback,
    )

    return response
