# AGENTS.md

## 1. 项目目标

本项目是一个 AI 辅助 React → Vue 3 代码迁移系统。

当前阶段目标是在有限时间内完成一个稳定、可演示、可解释的 MVP，而不是实现“任意 React 项目一键迁移”。

核心流程：

React 源码
→ AST 静态分析
→ AI 生成迁移计划
→ 人工确认或修改
→ AI 生成 Vue 3 代码
→ Vue 工具链验证
→ 验证失败时有限自动修复
→ 生成迁移报告

项目优先保证：

1. 流程可运行
2. 结果可验证
3. AI 行为可控制
4. 失败原因可追踪
5. 迁移过程可解释

不要为了增加功能数量而破坏核心闭环。

---

## 2. 技术栈

### 前端

- Vue 3
- TypeScript
- Vite
- Pinia

### 后端

- Python 3.11
- FastAPI
- LangGraph
- LangChain
- Pydantic
- SQLAlchemy
- SQLite

### Node Runner

- Node.js
- TypeScript
- Babel Parser
- Babel Traverse
- Vue Compiler SFC
- ESLint
- vue-tsc
- Vite

---

## 3. 项目目录职责

项目主要目录：

```text
react-vue-migrator/
├── AGENTS.md
├── README.md
├── frontend/
├── backend/
├── node-runner/
├── sandbox/
├── examples/
└── tests/
```

前端当前关键结构：

```text
frontend/src/
├── api/                  # FastAPI 请求封装
├── components/migration/ # 迁移工作台页面组件
├── router/               # 页面路由
├── types/                # 前端迁移任务类型
├── views/                # 页面级组件
├── App.vue
├── main.ts
└── style.css
```
