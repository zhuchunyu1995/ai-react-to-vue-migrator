from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MigrationTarget(BaseModel):
    """React 组件迁移的目标配置。"""

    # 目标前端框架，MVP 阶段固定为 Vue 3
    framework: str = "vue3"

    # 生成代码使用的语言
    language: str = "typescript"

    # Vue 组件代码风格：使用 <script setup>
    component_style: str = "script_setup"


class MigrationCreate(BaseModel):
    """创建迁移任务时，POST 接口接收的请求参数。"""

    # 输入文件名称，例如 UserList.tsx
    filename: str

    # 待迁移的 React/JSX/TSX 源代码
    source_code: str

    # Vue 目标代码的生成配置
    target: MigrationTarget


class MigrationResponse(BaseModel):
    """创建迁移任务后返回给前端的数据。"""

    # 允许直接读取 SQLAlchemy ORM 对象的属性并转换为响应模型
    model_config = ConfigDict(from_attributes=True)

    # 迁移任务的唯一标识，用于查询任务状态和恢复工作流
    id: str

    # 用户提交的 React 文件名称
    filename: str

    # 当前任务状态，例如 created、analyzing、completed
    status: str

    # 迁移任务的创建时间
    created_at: datetime
