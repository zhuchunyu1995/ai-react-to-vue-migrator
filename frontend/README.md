# React → Vue 迁移工作台前端

该目录是 AI 辅助 React → Vue 3 迁移系统的前端，使用 Vue 3、TypeScript 和 Vite。

## 当前页面

- `/`：迁移工作台首页；
- React/TSX 文件名与源码输入；
- Counter、UserList 示例载入；
- 创建迁移任务；
- 展示迁移工作流、当前状态和框架映射预览。
- 轮询到 `waiting_for_review` 时自动打开迁移计划审核弹窗；
- 展示结构化映射、风险、人工检查项和生成约束；
- 支持确认计划、填写反馈要求 AI 修改，以及主动终止任务；
- 修改后的迁移计划会再次打开审核面板，形成“反馈 → 修订 → 再审核”闭环。
- 审核状态已到但计划数据尚未返回时继续轮询，拿到计划后再暂停。
- 审核通过后继续展示生成、验证、自动修复和报告阶段的实时进度；
- 展示并支持复制、下载最终 Vue 3 SFC；
- 展示 SFC、ESLint、vue-tsc、Vite Build 等逐项验证结果；
- 展示迁移映射、风险和人工检查项，并支持下载 Markdown 报告。

开发服务器会将 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 关键目录

```text
src/
├── api/                  # 后端请求封装
├── components/migration/ # 首页迁移工作台组件
├── router/               # Vue Router
├── styles/               # 页面和迁移结果模块样式
├── types/                # 迁移任务类型
├── views/                # 页面
├── App.vue
├── main.ts
└── style.css
```

## 启动

```bash
pnpm install
pnpm dev
```

## 构建

```bash
pnpm build
```
