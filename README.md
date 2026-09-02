# React → Vue 3 AI 辅助迁移系统

一个基于 AI + AST 静态分析 + LangGraph 工作流的 React → Vue 3 代码迁移工具。

项目目标不是实现“任意 React 项目一键迁移”，而是先完成一个可用于面试演示的 MVP：

用户提交单个 React 函数组件，系统先进行源码分析，再生成迁移计划并等待人工确认；确认后生成 Vue 3 代码，并通过真实 Vue 工具链进行验证。如果验证失败，系统会根据错误信息进行有限次数的自动修复，最终输出完整迁移报告。

## 一、核心流程

```text
React 源码
    ↓
AST 静态分析
    ↓
生成迁移计划
    ↓
人工确认 / 修改
    ↓
生成 Vue 3 代码
    ↓
SFC / ESLint / 类型 / Build 验证
    ↓
验证失败 → AI 自动修复
    ↓
生成迁移报告
```

## 二、当前进度

- FastAPI 基础服务、异步数据库会话和迁移任务模型；
- 创建迁移任务与查询任务接口；
- LangGraph 和大模型基础链路；
- SQLite Checkpointer 与迁移计划人工审核恢复；
- Babel AST React 源码分析；
- Vue 3 代码生成、持久化和有限自动修复；
- SFC、ESLint、vue-tsc 与 Vite Build 自动验证；
- 结构化迁移报告和 Markdown 报告；
- Vue 3 迁移工作台、反馈修订式人工审核、进度轮询和结果展示。

## 三、关键目录

```text
react-vue-migrator/
├── backend/      # FastAPI、LangGraph、数据库和大模型调用
├── frontend/     # Vue 3 迁移工作台
├── node-runner/  # AST 分析和 Vue 工具链执行入口
├── sandbox/      # 隔离验证模板
├── examples/     # React 迁移样例
└── tests/        # 测试
```
