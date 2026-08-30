from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migrations import Migration
from app.repositories.migration import create_migration, get_migration_by_id
from app.schemas.migration import MigrationCreate, MigrationResponse


async def create_migration_task(
    session: AsyncSession,
    payload: MigrationCreate,
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
) -> MigrationResponse:
    """根据任务ID获取迁移任务。"""

    migration = await get_migration_by_id(
        session,
        task_id=task_id,
    )
    return MigrationResponse.model_validate(migration)
