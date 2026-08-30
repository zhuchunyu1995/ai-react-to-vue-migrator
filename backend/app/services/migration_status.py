from app.db.session import AsyncSessionLocal
from app.repositories.migration import update_migration_status


# POST 请求结束后，原来的 db 会话已经关闭，后台工作流不能继续使用它。
async def save_migration_status(
    task_id: int,
    status: str,
    current_node: str,
) -> None:
    """使用独立数据库会话保存工作流状态。"""

    async with AsyncSessionLocal() as session, session.begin():
        await update_migration_status(
            session=session,
            task_id=int(task_id),
            status=status,
            current_node=current_node,
        )
