from datetime import datetime
from typing import Any, Literal

from app.llm.schemas import MigrationPlan
from pydantic import BaseModel, ConfigDict, model_validator


class MigrationTarget(BaseModel):
    """迁移目标框架和语言。"""

    framework: Literal["vue3"] = "vue3"
    language: Literal["typescript"] = "typescript"
    component_style: Literal["script_setup"] = "script_setup"


class MigrationCreateRequest(BaseModel):
    """前端请求创建迁移任务时的请求体。"""

    # React 文件名
    filename: str

    # React 组件源代码
    source_code: str

    target: MigrationTarget


class MigrationResponse(BaseModel):
    """返回给前端的迁移任务详情。"""

    # 允许 Pydantic 直接读取 SQLAlchemy ORM 对象属性。
    model_config = ConfigDict(from_attributes=True)

    # 迁移任务唯一标识。
    # 用于查询状态以及恢复 LangGraph 工作流。
    id: int

    # 用户提交的 React 文件名。
    filename: str

    # 当前任务状态。
    # 例如 queued、analyzing、waiting_for_review、
    # validating、completed、failed。
    status: str

    # 当前正在执行的 LangGraph 节点。
    current_node: str | None = None

    # 任务创建时间。
    created_at: datetime

    # 任务最后更新时间。
    updated_at: datetime | None = None

    # AI 生成、等待用户审核的迁移计划。
    migration_plan: MigrationPlan | None = None

    # 用户确认或修改后的最终迁移计划。
    approved_plan: MigrationPlan | None = None

    # 用户审核时填写的反馈。
    review_feedback: str | None = None

    # 最终生成的 Vue 文件名。
    generated_filename: str | None = None

    # 最终生成的 Vue 代码。
    generated_code: str | None = None

    # AI 生成代码时返回的补充说明。
    generation_notes: list[str] | None = None

    # SFC、Lint、类型检查、Build 是否全部通过。
    validation_passed: bool | None = None

    # 完整代码验证结果。
    validation_result: dict[str, Any] | None = None

    # 最终迁移报告。
    migration_report: dict[str, Any] | None = None


class MigrationDetailResponse(MigrationResponse):
    """迁移任务详情。"""

    # 用户驳回迁移计划时填写的原因
    review_feedback: str | None = None


class MigrationReviewRequest(BaseModel):
    """人工审核迁移计划时提交的数据。"""

    action: Literal["approve", "request_changes", "cancel"]

    # 通过时提交最终确认的计划
    migration_plan: MigrationPlan | None = None

    # 要求修改时填写具体反馈
    feedback: str | None = None

    @model_validator(mode="after")
    def validate_review_content(self) -> "MigrationReviewRequest":
        if self.action == "approve" and self.migration_plan is None:
            raise ValueError("通过审核时 migration_plan 不能为空")

        if self.action == "request_changes" and not (self.feedback or "").strip():
            raise ValueError("要求修改计划时 feedback 不能为空")

        return self
