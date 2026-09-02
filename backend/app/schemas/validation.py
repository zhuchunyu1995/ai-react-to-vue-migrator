from typing import Literal

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """单条验证错误。"""

    stage: Literal[
        "sfc_parse",
        "script_compile",
        "template_compile",
        "migration_rule",
        "lint",
        "type_check",
        "build",
        "runner",
    ]

    message: str
    line: int | None = None
    column: int | None = None


class VueValidationResult(BaseModel):
    """完整 Vue 验证结果。"""

    success: bool

    checks: dict[str, bool] = Field(default_factory=dict)

    errors: list[ValidationIssue] = Field(default_factory=list)

    details: dict[str, str] = Field(default_factory=dict)
