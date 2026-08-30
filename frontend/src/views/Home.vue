<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { createMigration } from "@/api/migration";
import AppHeader from "@/components/migration/AppHeader.vue";
import SourceInputPanel from "@/components/migration/SourceInputPanel.vue";
import WorkflowStepper from "@/components/migration/WorkflowStepper.vue";
import { useMigrationPolling } from "@/composables/useMigrationPolling";
import type { MigrationPhase, MigrationStatus } from "@/types/migration";
const { task, isPolling, pollingError, startPolling } = useMigrationPolling();

const examples = {
  counter: {
    filename: "Counter.tsx",
    source: `import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}`,
  },
  userList: {
    filename: "UserList.tsx",
    source: `import { useMemo, useState } from "react";

interface User {
  id: string;
  name: string;
}

export function UserList({ users }: { users: User[] }) {
  const [keyword, setKeyword] = useState("");
  const filteredUsers = useMemo(
    () => users.filter((user) => user.name.includes(keyword)),
    [users, keyword],
  );

  return (
    <section>
      <input
        value={keyword}
        onChange={(event) => setKeyword(event.target.value)}
      />
      <ul>
        {filteredUsers.map((user) => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </section>
  );
}`,
  },
};

const filename = ref(examples.userList.filename);
const sourceCode = ref(examples.userList.source);
const phase = ref<MigrationPhase>("idle");
const taskId = ref<number | null>(null);
const statusMessage = ref(
  "填写组件源码后，系统会先生成迁移计划，不会直接覆盖代码。",
);
const errorMessage = ref("");

const isBusy = computed(() =>
  ["submitting", "analyzing", "planning", "generating", "validating"].includes(
    phase.value,
  ),
);

function loadExample(exampleKey: keyof typeof examples) {
  const example = examples[exampleKey];
  filename.value = example.filename;
  sourceCode.value = example.source;
  phase.value = "idle";
  taskId.value = null;
  errorMessage.value = "";
  statusMessage.value = "示例已载入，可以开始分析迁移路径。";
}

function clearSource() {
  filename.value = "";
  sourceCode.value = "";
  phase.value = "idle";
  taskId.value = null;
  errorMessage.value = "";
  statusMessage.value = "输入一个 React 函数组件开始迁移。";
}

async function submitMigration() {
  errorMessage.value = "";

  if (!filename.value.trim() || !sourceCode.value.trim()) {
    errorMessage.value = "请填写文件名并粘贴 React 组件源码。";
    return;
  }

  phase.value = "submitting";
  statusMessage.value = "正在创建迁移任务…";

  try {
    const response = await createMigration({
      filename: filename.value.trim(),
      source_code: sourceCode.value,
      target: {
        framework: "vue3",
        language: "typescript",
        component_style: "script_setup",
      },
    });

    taskId.value = response.id;
    phase.value = "analyzing";

    startPolling(taskId.value);

    statusMessage.value = taskId.value
      ? "任务已创建，正在解析 React 源码。"
      : "接口已接收任务，等待后端返回任务 ID。";
  } catch (error) {
    phase.value = "failed";
    errorMessage.value =
      error instanceof Error ? error.message : "创建迁移任务失败，请稍后重试。";
    statusMessage.value = "任务未创建，源码仍保留在编辑器中。";
  }
}

/**
 * 后端状态对应的页面提示文案。
 */
const statusMessages: Record<MigrationStatus, string> = {
  queued: "迁移任务已进入执行队列。",
  analyzing: "正在解析 React 源码和 AST。",
  planning: "源码分析完成，正在生成迁移计划。",
  waiting_for_review: "迁移计划已生成，请确认后继续。",
  generating: "正在根据迁移计划生成 Vue 组件。",
  validating: "正在执行 Vue SFC、Lint 和类型检查。",
  repairing: "检查发现问题，正在尝试自动修复。",
  completed: "React 组件迁移已经完成。",
  failed: "迁移任务执行失败。",
};

/**
 * 监听轮询得到的最新任务数据。
 *
 * 每次 useMigrationPolling 更新 task.value，
 * 这里都会自动更新页面 phase 和提示文案。
 */
watch(task, (latestTask) => {
  if (!latestTask) {
    return;
  }

  // 保存后端最新返回的任务 ID
  taskId.value = latestTask.id;

  // 将后端 status 同步给步骤条
  phase.value = latestTask.status;

  // 更新页面提示信息
  statusMessage.value = statusMessages[latestTask.status];

  if (latestTask.status === "failed") {
    errorMessage.value = "迁移执行失败，请检查后端日志。";
  } else {
    errorMessage.value = "";
  }
});
</script>

<template>
  <div class="home-page">
    <AppHeader />

    <main>
      <section class="hero" aria-labelledby="page-title">
        <div class="hero-copy">
          <p class="eyebrow">AI-assisted migration workspace</p>
          <h1 id="page-title">把 React 组件迁移成可验证的 Vue 3 代码</h1>
          <p class="hero-description">
            AST 提取事实，AI 规划语义转换，人工确认关键决策，再通过 Vue
            工具链验证与有限自动修复。
          </p>
        </div>

        <ul class="hero-tags" aria-label="迁移能力">
          <li>Human-in-the-loop</li>
          <li>Vue 3 Script Setup</li>
          <li>Lint · Type · Build</li>
        </ul>
      </section>

      <section id="workspace" class="workspace" aria-label="迁移工作台">
        <SourceInputPanel
          v-model:filename="filename"
          v-model:source-code="sourceCode"
          :busy="isBusy"
          :error-message="errorMessage"
          @load-example="loadExample"
          @clear="clearSource"
          @submit="submitMigration"
        />

        <WorkflowStepper
          :phase="phase"
          :task-id="taskId"
          :message="statusMessage"
        />
      </section>

      <section class="principles" aria-labelledby="principles-title">
        <div class="section-heading">
          <p class="eyebrow">Built for explainability</p>
          <h2 id="principles-title">每一步都有依据，也保留人工判断</h2>
        </div>

        <div class="principle-grid">
          <article>
            <span>01</span>
            <h3>确定性分析</h3>
            <p>Babel 负责识别 props、Hooks 和 JSX 模式，减少模型猜测。</p>
          </article>
          <article>
            <span>02</span>
            <h3>计划先于生成</h3>
            <p>先展示映射与风险，由你确认后再生成 Vue 组件。</p>
          </article>
          <article>
            <span>03</span>
            <h3>真实工具验证</h3>
            <p>SFC、ESLint、vue-tsc 与 Vite Build 共同验证迁移结果。</p>
          </article>
        </div>
      </section>
    </main>

    <footer class="page-footer">
      <p>React → Vue 3 Migration Workspace</p>
      <p>当前版本聚焦单个 React 函数组件的可解释迁移。</p>
    </footer>
  </div>
</template>

<style scoped src="../styles/home.css"></style>
