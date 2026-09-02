<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { createMigration } from "@/api/migration";
import AppHeader from "@/components/migration/AppHeader.vue";
import MigrationResultPanel from "@/components/migration/MigrationResultPanel.vue";
import MigrationReviewDialog from "@/components/migration/MigrationReviewDialog.vue";
import SourceInputPanel from "@/components/migration/SourceInputPanel.vue";
import WorkflowStepper from "@/components/migration/WorkflowStepper.vue";
import { useMigrationPolling } from "@/composables/useMigrationPolling";
import { useMigrationReview } from "@/composables/useMigrationReview";
import {
  migrationExamples,
  migrationStatusMessages,
} from "@/constants/migration";
import type { MigrationPhase } from "@/types/migration";

const { task, pollingError, startPolling, stopPolling, resetPolling } =
  useMigrationPolling();

const filename = ref(migrationExamples.userList.filename);
const sourceCode = ref(migrationExamples.userList.source);
const phase = ref<MigrationPhase>("idle");
const taskId = ref<number | null>(null);
const statusMessage = ref(
  "填写组件源码后，系统会先生成迁移计划，不会直接覆盖代码。",
);
const errorMessage = ref("");

const {
  reviewDialogVisible,
  reviewPlan,
  reviewSubmitting,
  reviewError,
  resetReviewState,
  handleReviewTask,
  approvePlan,
  requestPlanChanges,
  cancelMigration,
} = useMigrationReview({
  taskId,
  phase,
  statusMessage,
  startPolling,
  stopPolling,
});

const isBusy = computed(
  () =>
    !["idle", "completed", "failed", "rejected", "cancelled"].includes(
      phase.value,
    ),
);
const hasResult = computed(() =>
  Boolean(
    task.value?.generated_code ||
      task.value?.validation_result ||
      task.value?.migration_report,
  ),
);

function loadExample(exampleKey: keyof typeof migrationExamples) {
  resetPolling();
  const example = migrationExamples[exampleKey];
  filename.value = example.filename;
  sourceCode.value = example.source;
  phase.value = "idle";
  taskId.value = null;
  resetReviewState();
  errorMessage.value = "";
  statusMessage.value = "示例已载入，可以开始分析迁移路径。";
}

function clearSource() {
  resetPolling();
  filename.value = "";
  sourceCode.value = "";
  phase.value = "idle";
  taskId.value = null;
  resetReviewState();
  errorMessage.value = "";
  statusMessage.value = "输入一个 React 函数组件开始迁移。";
}

async function submitMigration() {
  resetPolling();
  taskId.value = null;
  errorMessage.value = "";
  resetReviewState();

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
watch(task, (latestTask) => {
  if (!latestTask) {
    return;
  }

  taskId.value = latestTask.id;
  phase.value = latestTask.status;

  handleReviewTask(latestTask);

  statusMessage.value = migrationStatusMessages[latestTask.status];

  if (latestTask.status === "failed") {
    const firstError = latestTask.validation_result?.errors[0];
    errorMessage.value = firstError
      ? `迁移执行失败：${firstError.message}`
      : "迁移执行失败，请检查后端日志。";
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

      <div
        v-if="phase === 'waiting_for_review' && !reviewDialogVisible"
        class="review-ready-banner"
        role="status"
      >
        <p>迁移计划正在等待你的确认，工作流已安全暂停。</p>
        <button type="button" @click="reviewDialogVisible = true">
          查看迁移计划
        </button>
      </div>

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
          :current-node="task?.current_node ?? null"
          :message="statusMessage"
        />
      </section>

      <p v-if="pollingError" class="polling-error" role="alert">
        {{ pollingError }}，页面会继续自动重试。
      </p>

      <MigrationResultPanel v-if="task && hasResult" :task="task" />

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

    <MigrationReviewDialog
      :open="reviewDialogVisible"
      :task-id="taskId"
      :plan="reviewPlan"
      :submitting="reviewSubmitting"
      :error-message="reviewError"
      @close="reviewDialogVisible = false"
      @approve="approvePlan"
      @request-changes="requestPlanChanges"
      @cancel="cancelMigration"
    />
  </div>
</template>

<style scoped src="../styles/home.css"></style>
