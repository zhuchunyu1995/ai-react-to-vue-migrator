from datetime import datetime

from app.db.base import Base
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Migration(Base):
    """React → Vue 迁移任务。"""

    __tablename__ = "migrations"

    # 任务主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 用户提交的 React 文件名
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # React 原始源码
    source_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 当前业务状态
    status: Mapped[str] = mapped_column(
        String(50),
        default="queued",
        nullable=False,
    )

    # 当前执行到的 LangGraph 节点
    current_node: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
