<script setup lang="ts">
import { computed } from "vue";

import type { MigrationPhase, WorkflowStepState } from "@/types/migration";

const props = defineProps<{
  phase: MigrationPhase;
  taskId: number | null;
  message: string;
}>();

const definitions = [
  ["analyzing", "解析 React 源码", "提取 props、Hooks 与 JSX 模式"],
  ["planning", "生成迁移计划", "形成结构化映射与风险清单"],
  ["waiting_for_review", "等待人工确认", "确认关键语义后再继续生成"],
  ["generating", "生成 Vue 组件", "输出 Vue 3 Script Setup SFC"],
  ["validating", "工具链验证", "执行 SFC、Lint、Type 与 Build"],
  ["completed", "生成迁移报告", "汇总映射、修复和人工处理项"],
] as const;

const phaseOrder: Record<MigrationPhase, number> = {
  idle: -1,
  submitting: 0,
  queued: 0,
  analyzing: 0,
  planning: 1,
  waiting_for_review: 2,
  generating: 3,
  validating: 4,
  repairing: 4,
  completed: 6,
  failed: -1,
};

const steps = computed(() => {
  const currentIndex = phaseOrder[props.phase];

  return definitions.map(([id, label, description], index) => {
    let state: WorkflowStepState = "pending";
    if (props.phase === "completed" || index < currentIndex) state = "done";
    if (index === currentIndex && props.phase !== "completed") state = "active";
    if (props.phase === "failed" && index === 0) state = "error";

    return { id, label, description, state };
  });
});
</script>

<template>
  <aside class="workflow-panel" aria-labelledby="workflow-title">
    <div class="panel-heading">
      <div>
        <p>02 / Workflow</p>
        <h2 id="workflow-title">迁移执行路径</h2>
      </div>
      <span class="status-pill" :class="phase">
        {{ phase === "idle" ? "等待任务" : phase.replaceAll("_", " ") }}
      </span>
    </div>

    <div class="task-message" aria-live="polite">
      <span class="message-icon" aria-hidden="true">i</span>
      <div>
        <strong>{{ taskId ? `Task ${taskId}` : "当前状态" }}</strong>
        <p>{{ message }}</p>
      </div>
    </div>

    <ol class="step-list">
      <li
        v-for="(step, index) in steps"
        :key="step.id"
        :class="step.state"
        :aria-current="step.state === 'active' ? 'step' : undefined"
      >
        <span class="step-marker" aria-hidden="true">
          <template v-if="step.state === 'done'">✓</template>
          <template v-else-if="step.state === 'error'">!</template>
          <template v-else>{{ index + 1 }}</template>
        </span>
        <div>
          <strong>{{ step.label }}</strong>
          <p>{{ step.description }}</p>
        </div>
      </li>
    </ol>

    <div class="mapping-preview">
      <div class="preview-heading">
        <span>映射预览</span>
        <small>计划阶段确认</small>
      </div>
      <ul>
        <li><code>useState</code><span>→</span><code>ref</code></li>
        <li><code>useMemo</code><span>→</span><code>computed</code></li>
        <li><code>array.map</code><span>→</span><code>v-for</code></li>
      </ul>
    </div>
  </aside>
</template>

<style scoped src="../../styles/workflow-stepper.css"></style>
