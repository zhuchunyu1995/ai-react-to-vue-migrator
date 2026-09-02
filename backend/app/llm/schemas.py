# 存放大模型结构化输入、输出对应的 Pydantic 模型。
# 主要用于限制模型不能随意返回文本，必须按照规定字段返回。
# 例如迁移计划：
from typing import Literal

from pydantic import BaseModel, Field


class MigrationMapping(BaseModel):
    """一个 React 到 Vue 的迁移映射。"""

    category: Literal[
        "state",
        "effect",
        "props",
        "event",
        "template",
        "dependency",
        "other",
    ]

    # React 中的源模式
    source: str

    # Vue 中的目标模式
    target: str

    # 做出此映射的原因
    reason: str

    # 对应的源代码行号
    source_line: int | None = None

    # 规则引擎或者大模型产生的结论
    strategy: Literal["rule", "llm"]

    # 置信度
    confidence: float = Field(ge=0, le=1)

    # 是否需要人工确认
    needs_review: bool = False


class MigrationPlan(BaseModel):
    """React 组件迁移计划。"""

    component_name: str

    target_framework: Literal["vue3"] = "vue3"

    target_language: Literal["typescript"] = "typescript"

    component_style: Literal["script_setup"] = "script_setup"

    # React 到 Vue 的具体映射
    mappings: list[MigrationMapping]

    # Vue 项目需要安装或替换的依赖
    dependencies: list[str]

    # 可能影响迁移正确性的风险
    risks: list[str]

    # 必须由用户确认的问题
    manual_checks: list[str]

    # 代码生成阶段必须遵守的限制
    generation_constraints: list[str]


class VueCodeResult(BaseModel):
    """大模型生成的 Vue 组件结果。"""

    # 生成的 Vue 文件名
    filename: str

    # 完整的 Vue SFC 代码
    code: str

    # 生成阶段需要人工关注的说明
    notes: list[str]


class RepairCodeResult(BaseModel):
    """大模型修复 Vue 代码后的结构化结果。"""

    # 修复后的完整 Vue SFC 代码。
    code: str = Field(..., min_length=1)

    # 本次具体修改了什么。
    changes: list[str] = Field(default_factory=list)

    # 仍需要注意的问题。
    notes: list[str] = Field(default_factory=list)
