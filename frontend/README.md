# React → Vue 迁移工作台前端

该目录是 AI 辅助 React → Vue 3 迁移系统的前端，使用 Vue 3、TypeScript 和 Vite。

## 当前页面

- `/`：迁移工作台首页；
- React/TSX 文件名与源码输入；
- Counter、UserList 示例载入；
- 创建迁移任务；
- 展示迁移工作流、当前状态和框架映射预览。

开发服务器会将 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 关键目录

```text
src/
├── api/                  # 后端请求封装
├── components/migration/ # 首页迁移工作台组件
├── router/               # Vue Router
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
