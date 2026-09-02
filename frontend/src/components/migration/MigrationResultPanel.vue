<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  MigrationTask,
  MigrationValidationResult,
} from "@/types/migration";

type ResultTab = "code" | "validation" | "report";

const props = defineProps<{
  task: MigrationTask;
}>();

const activeTab = ref<ResultTab>("code");
const copied = ref(false);

const report = computed(() => props.task.migration_report ?? null);

const validation = computed<MigrationValidationResult | null>(() => {
  if (props.task.validation_result) return props.task.validation_result;
  if (!report.value) return null;

  return {
    success: report.value.validation.passed,
    checks: report.value.validation.checks,
    errors: report.value.validation.errors,
    details: report.value.validation.details,
  };
});

const checks = computed(() => Object.entries(validation.value?.checks ?? {}));
const passedCheckCount = computed(
  () => checks.value.filter(([, passed]) => passed).length,
);
const mappings = computed(
  () => report.value?.mappings ?? props.task.approved_plan?.mappings ?? [],
);
const repairCount = computed(() => report.value?.summary.repair_count ?? 0);

const checkLabels: Record<string, string> = {
  sfc_parse: "SFC 解析",
  script_compile: "Script 编译",
  template_compile: "模板编译",
  migration_rule: "迁移规则",
  lint: "ESLint",
  type_check: "类型检查",
  build: "Vite Build",
};

async function copyGeneratedCode() {
  const code = props.task.generated_code;
  if (!code) return;

  await navigator.clipboard.writeText(code);
  copied.value = true;
  window.setTimeout(() => {
    copied.value = false;
  }, 1800);
}

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function downloadGeneratedCode() {
  if (!props.task.generated_code) return;
  downloadText(
    props.task.generated_filename ?? "GeneratedComponent.vue",
    props.task.generated_code,
    "text/plain;charset=utf-8",
  );
}

function downloadReport() {
  if (!report.value?.markdown) return;
  const componentName = report.value.summary.component_name || "migration";
  downloadText(
    `${componentName}-migration-report.md`,
    report.value.markdown,
    "text/markdown;charset=utf-8",
  );
}
</script>

<template>
  <section id="migration-result" class="result-panel" aria-labelledby="result-title">
    <header class="result-header">
      <div>
        <p class="result-eyebrow">03 / Migration Result</p>
        <h2 id="result-title">迁移产物与验证报告</h2>
        <p>查看最终 Vue 组件、真实工具链结果和迁移决策记录。</p>
      </div>
      <span
        class="result-status"
        :class="{ success: task.status === 'completed', danger: task.status === 'failed' }"
      >
        {{ task.status === "completed" ? "迁移完成" : task.status.replaceAll("_", " ") }}
      </span>
    </header>

    <div class="result-metrics">
      <article>
        <span>工具链</span>
        <strong>{{ passedCheckCount }}/{{ checks.length || 7 }}</strong>
        <small>checks passed</small>
      </article>
      <article>
        <span>迁移映射</span>
        <strong>{{ mappings.length }}</strong>
        <small>decisions recorded</small>
      </article>
      <article>
        <span>自动修复</span>
        <strong>{{ repairCount }}</strong>
        <small>repair rounds</small>
      </article>
      <article>
        <span>输出文件</span>
        <strong class="filename-metric">
          {{ task.generated_filename ?? "等待生成" }}
        </strong>
        <small>Vue 3 SFC</small>
      </article>
    </div>

    <div class="result-tabs" role="tablist" aria-label="迁移结果">
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'code'"
        :class="{ active: activeTab === 'code' }"
        :disabled="!task.generated_code"
        @click="activeTab = 'code'"
      >
        Vue 代码
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'validation'"
        :class="{ active: activeTab === 'validation' }"
        :disabled="!validation"
        @click="activeTab = 'validation'"
      >
        自动验证
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'report'"
        :class="{ active: activeTab === 'report' }"
        :disabled="!report"
        @click="activeTab = 'report'"
      >
        迁移报告
      </button>
    </div>

    <div v-if="activeTab === 'code'" class="result-content code-result">
      <div class="artifact-toolbar">
        <div>
          <span class="vue-dot"></span>
          <strong>{{ task.generated_filename }}</strong>
        </div>
        <div class="artifact-actions">
          <button type="button" @click="copyGeneratedCode">
            {{ copied ? "已复制" : "复制代码" }}
          </button>
          <button type="button" @click="downloadGeneratedCode">下载 .vue</button>
        </div>
      </div>
      <pre><code>{{ task.generated_code }}</code></pre>
      <ul v-if="task.generation_notes?.length" class="generation-notes">
        <li v-for="note in task.generation_notes" :key="note">{{ note }}</li>
      </ul>
    </div>

    <div v-else-if="activeTab === 'validation' && validation" class="result-content">
      <div class="validation-grid">
        <article v-for="([name, passed]) in checks" :key="name" :class="{ passed }">
          <span aria-hidden="true">{{ passed ? "✓" : "!" }}</span>
          <div>
            <strong>{{ checkLabels[name] ?? name }}</strong>
            <small>{{ passed ? "检查通过" : "需要处理" }}</small>
          </div>
        </article>
      </div>

      <div v-if="validation.errors.length" class="validation-errors">
        <h3>验证错误</h3>
        <article v-for="(error, index) in validation.errors" :key="`${error.stage}-${index}`">
          <strong>{{ checkLabels[error.stage] ?? error.stage }}</strong>
          <p>{{ error.message }}</p>
          <small v-if="error.line">第 {{ error.line }} 行 · 第 {{ error.column ?? 1 }} 列</small>
        </article>
      </div>

      <div v-else class="validation-success">
        <span aria-hidden="true">✓</span>
        <div>
          <strong>生成代码已通过全部自动检查</strong>
          <p>SFC、代码规范、类型系统和生产构建均未发现阻断问题。</p>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'report' && report" class="result-content report-result">
      <div class="report-heading">
        <div>
          <span>Migration report · v{{ report.version }}</span>
          <h3>{{ report.summary.component_name }}</h3>
          <p>{{ report.summary.source_filename }} → {{ report.summary.generated_filename }}</p>
        </div>
        <button type="button" @click="downloadReport">下载 Markdown</button>
      </div>

      <section class="report-section">
        <h3>迁移映射</h3>
        <div class="report-mappings">
          <article v-for="(mapping, index) in mappings" :key="`${mapping.category}-${index}`">
            <span>{{ mapping.category }}</span>
            <div><code>{{ mapping.source }}</code><b>→</b><code>{{ mapping.target }}</code></div>
            <p>{{ mapping.reason }}</p>
          </article>
        </div>
      </section>

      <div class="report-columns">
        <section>
          <h3>风险提示</h3>
          <ul v-if="report.risks.length">
            <li v-for="risk in report.risks" :key="risk">{{ risk }}</li>
          </ul>
          <p v-else>未记录额外风险。</p>
        </section>
        <section>
          <h3>人工检查项</h3>
          <ul v-if="report.manual_checks.length">
            <li v-for="item in report.manual_checks" :key="item">{{ item }}</li>
          </ul>
          <p v-else>没有额外人工检查项。</p>
        </section>
      </div>
    </div>
  </section>
</template>

<style scoped src="../../styles/migration-result-panel.css"></style>
<style scoped src="../../styles/migration-report.css"></style>
