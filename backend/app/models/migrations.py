from datetime import datetime
from typing import Any

from app.db.base import Base
from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
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

    # AI 生成、等待用户确认的迁移计划

    migration_plan: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # 用户最终确认或修改后的计划
    approved_plan: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # 用户驳回迁移计划时填写的原因
    review_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 最终生成的 Vue 文件名
    generated_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # 大模型生成的完整 Vue SFC
    generated_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 代码生成阶段产生的说明
    generation_notes: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # Vue 代码是否验证通过。
    validation_passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # 完整验证结果。
    validation_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # 验证错误列表。
    validation_errors: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # 最终迁移报告。
    migration_report: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
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
