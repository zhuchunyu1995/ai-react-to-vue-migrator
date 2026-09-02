from contextlib import asynccontextmanager

import aiosqlite
from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import async_engine
from app.graph.builder import create_migration_graph
from app.routes.migrations import router as migrations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """初始化并关闭 LangGraph 的 SQLite Checkpointer。"""
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    settings = get_settings()
    checkpoint_path = settings.checkpoint_database_path
    # 确保目录存在
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建 SQLite 连接并初始化 AsyncSqliteSaver
    connection = await aiosqlite.connect(str(checkpoint_path))

    # 初始化 Checkpointer
    checkpointer = AsyncSqliteSaver(connection)

    await checkpointer.setup()

    # 首次执行和人工审核恢复必须复用同一个持久化图实例
    app.state.migration_graph = create_migration_graph(checkpointer)

    try:
        yield
    finally:
        await connection.close()


app = FastAPI(lifespan=lifespan)


app.include_router(migrations_router)
