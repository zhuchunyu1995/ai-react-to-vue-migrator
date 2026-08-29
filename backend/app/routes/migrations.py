from typing import Annotated

from db.session import get_db
from fastapi import APIRouter, Depends, Path
from requests import Session
from schemas.migration import MigrationCreate

router = APIRouter(prefix="/api/migrations", tags=["migrations"])


@router.get("/{task_id}")
async def get_migration_task(
    db: Annotated[Session, Depends(get_db)],
    task_id: str = Path(..., description="迁移任务ID"),
):
    print(task_id)
    return {"taskId": task_id}


# 创建迁移任务
@router.post("/")
async def create_migration_task(
    db: Annotated[Session, Depends(get_db)],
    request_body: MigrationCreate,
):
    print(request_body)
    return {"body": request_body}
