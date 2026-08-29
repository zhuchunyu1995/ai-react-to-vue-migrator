# 存放大模型结构化输入、输出对应的 Pydantic 模型。
# 主要用于限制模型不能随意返回文本，必须按照规定字段返回。
# 例如迁移计划：
from pydantic import BaseModel, Field


class MigrationMapping(BaseModel):
    source: str
    target: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class MigrationPlan(BaseModel):
    summary: str
    mappings: list[MigrationMapping]
    risks: list[str]
    manual_actions: list[str]
