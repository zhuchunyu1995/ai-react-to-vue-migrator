from app.db.session import AsyncSessionLocal
from app.repositories.migration import update_generated_code


async def save_generated_result(
    *,
    task_id: int,
    generated_filename: str,
    generated_code: str,
    generation_notes: list[str],
) -> None:
    """使用独立数据库会话保存 Vue 生成结果。"""

    # 工作流运行在 BackgroundTasks 中，
    # 不能继续使用创建任务接口中的数据库 session。
    async with AsyncSessionLocal() as session, session.begin():
        await update_generated_code(
            session,
            task_id,
            generated_filename=generated_filename,
            generated_code=generated_code,
            generation_notes=generation_notes,
        )
