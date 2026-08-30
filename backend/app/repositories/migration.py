from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
        status="created",
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
