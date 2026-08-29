from typing import Any, TypedDict


class MigrationState(TypedDict, total=False):
    """React → Vue 迁移工作流的共享状态。"""

    # 当前迁移任务的唯一标识，用于查询任务、保存状态和关联工作流 Checkpoint
    task_id: str

    # 用户提交的 React 源文件名，例如 UserList.tsx
    filename: str

    # 用户提交的 React 原始源码
    source_code: str

    # React 源码经过 Babel AST 分析后的结构化结果
    # 例如：组件名、props、Hooks、事件、渲染模式、不支持能力等
    source_analysis: dict[str, Any]

    # AI 根据源码和 AST 分析结果生成的迁移计划
    # 例如：useState → ref、useMemo → computed、children → slot
    migration_plan: dict[str, Any]

    # 当前工作流正在执行或最后执行完成的节点名称
    # 例如：analyze_source、create_plan、human_review
    current_node: str

    # 当前迁移任务的业务状态，主要用于前端展示任务进度
    # 例如：created、analyzing、planning、waiting_for_review、completed
    status: str
