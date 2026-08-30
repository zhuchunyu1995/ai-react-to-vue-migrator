from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.graph.builder import run_migration_graph
from app.schemas.migration import MigrationCreate
from app.services import migration

router = APIRouter(prefix="/api/migrations", tags=["migrations"])


@router.get("/{task_id}")
async def get_migration_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: int = Path(..., description="迁移任务ID"),
):
    response = await migration.get_migration_task(db, task_id=task_id)
    return {
        "id": response.id,
        "filename": response.filename,
        "status": response.status,
        "current_node": response.current_node,
        "created_at": response.created_at,
    }


@router.post("/", status_code=202)
async def create_migration_route(
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: MigrationCreate,
    background_tasks: BackgroundTasks,
):
    response = await migration.create_migration_task(
        db,
        payload=payload,
    )

    background_tasks.add_task(
        run_migration_graph,
        response.id,
        payload.filename,
        payload.source_code,
    )

    return response
