import asyncio

from app.db.base import Base
from app.db.session import async_engine

# 必须导入具体 ORM 模型，否则 Base.metadata 不知道有哪些表
from app.models.migrations import Migration


async def init_db() -> None:
    """创建当前尚不存在的数据库表。"""

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        print(Migration)

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
