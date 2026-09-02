<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { MigrationPlan } from "@/types/migration";

const props = defineProps<{
  open: boolean;
  taskId: number | null;
  plan: MigrationPlan | null;
  submitting: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{
  approve: [plan: MigrationPlan];
  requestChanges: [feedback: string];
  cancel: [];
  close: [];
}>();

type ActionMode = "review" | "revision" | "cancel";

const actionMode = ref<ActionMode>("review");
const revisionFeedback = ref("");

const reviewCount = computed(
  () => props.plan?.mappings.filter((item) => item.needs_review).length ?? 0,
);

watch(
  () => props.open,
  (open) => {
    if (open) {
      actionMode.value = "review";
      revisionFeedback.value = "";
    }
  },
);

function approvePlan() {
  if (props.plan) {
    emit("approve", props.plan);
  }
}

function requestChanges() {
  const feedback = revisionFeedback.value.trim();
  if (feedback) {
    emit("requestChanges", feedback);
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="review-backdrop">
      <section
        class="review-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-dialog-title"
      >
        <header class="review-header">
          <div>
            <p class="review-eyebrow">03 / Human Review</p>
            <h2 id="review-dialog-title">确认迁移计划后继续</h2>
            <p>
              AI 已完成语义映射。请重点检查标记项和风险，再决定是否生成 Vue
              代码。
            </p>
          </div>
          <button
            class="close-button"
            type="button"
            :disabled="submitting"
            aria-label="暂时关闭审核窗口"
            @click="emit('close')"
          >
            ×
          </button>
        </header>

        <div v-if="plan" class="review-content">
          <div class="plan-summary">
            <div>
              <span>组件</span>
              <strong>{{ plan.component_name }}</strong>
            </div>
            <div>
              <span>目标</span>
              <strong>Vue 3 · TypeScript</strong>
            </div>
            <div>
              <span>映射</span>
              <strong>{{ plan.mappings.length }} 项</strong>
            </div>
            <div>
              <span>需重点确认</span>
              <strong :class="{ attention: reviewCount > 0 }">
                {{ reviewCount }} 项
              </strong>
            </div>
          </div>

          <section class="review-section" aria-labelledby="mapping-title">
            <div class="section-title-row">
              <h3 id="mapping-title">迁移映射</h3>
              <span>{{ plan.mappings.length }} mappings</span>
            </div>
            <div class="mapping-list">
              <article
                v-for="(mapping, index) in plan.mappings"
                :key="`${mapping.category}-${index}`"
                class="mapping-item"
                :class="{ flagged: mapping.needs_review }"
              >
                <div class="mapping-meta">
                  <span class="category-badge">{{ mapping.category }}</span>
                  <span v-if="mapping.needs_review" class="review-badge">
                    需要确认
                  </span>
                  <small
                    >{{ Math.round(mapping.confidence * 100) }}%
                    confidence</small
                  >
                </div>
                <div class="mapping-code">
                  <code>{{ mapping.source }}</code>
                  <span aria-hidden="true">→</span>
                  <code>{{ mapping.target }}</code>
                </div>
                <p>{{ mapping.reason }}</p>
              </article>
            </div>
          </section>

          <div class="review-columns">
            <section class="review-section compact">
              <h3>风险提示</h3>
              <ul v-if="plan.risks.length">
                <li v-for="risk in plan.risks" :key="risk">{{ risk }}</li>
              </ul>
              <p v-else class="empty-copy">未发现额外迁移风险。</p>
            </section>

            <section class="review-section compact">
              <h3>人工检查项</h3>
              <ul v-if="plan.manual_checks.length">
                <li v-for="item in plan.manual_checks" :key="item">
                  {{ item }}
                </li>
              </ul>
              <p v-else class="empty-copy">没有必须人工补充的检查项。</p>
            </section>
          </div>

          <details
            v-if="plan.generation_constraints.length"
            class="constraints"
          >
            <summary>查看代码生成约束</summary>
            <ul>
              <li
                v-for="constraint in plan.generation_constraints"
                :key="constraint"
              >
                {{ constraint }}
              </li>
            </ul>
          </details>
        </div>

        <div v-else class="plan-unavailable" role="status">
          <strong>正在等待迁移计划数据</strong>
          <p>
            任务已经进入审核阶段，但查询接口还没有返回
            <code>migration_plan</code>。
          </p>
        </div>

        <p v-if="errorMessage" class="review-error" role="alert">
          {{ errorMessage }}
        </p>

        <div v-if="actionMode === 'revision'" class="revision-form">
          <label for="revision-feedback">希望 AI 修改什么？</label>
          <textarea
            id="revision-feedback"
            v-model="revisionFeedback"
            rows="3"
            placeholder="例如：请重新检查 props 响应性和 onChange 的事件语义。"
            :disabled="submitting"
          ></textarea>
          <p>提交后会重新生成完整计划，并再次回到人工审核。</p>
        </div>

        <div v-else-if="actionMode === 'cancel'" class="cancel-confirmation">
          <strong>确定终止这个迁移任务吗？</strong>
          <p>终止后不会继续生成 Vue 代码，但输入的 React 源码仍会保留。</p>
        </div>

        <footer class="review-actions">
          <button
            v-if="actionMode === 'review'"
            class="cancel-button"
            type="button"
            :disabled="submitting"
            @click="actionMode = 'cancel'"
          >
            终止任务
          </button>
          <button
            v-if="actionMode === 'review'"
            class="revision-button"
            type="button"
            :disabled="submitting || !plan"
            @click="actionMode = 'revision'"
          >
            要求 AI 修改
          </button>
          <button
            v-if="actionMode === 'review'"
            class="approve-button"
            type="button"
            :disabled="submitting || !plan"
            @click="approvePlan"
          >
            {{ submitting ? "正在提交…" : "确认计划并继续" }}
            <span v-if="!submitting" aria-hidden="true">→</span>
          </button>
          <template v-else-if="actionMode === 'revision'">
            <button
              class="secondary-button"
              type="button"
              :disabled="submitting"
              @click="actionMode = 'review'"
            >
              返回
            </button>
            <button
              class="revision-submit-button"
              type="button"
              :disabled="submitting || !revisionFeedback.trim()"
              @click="requestChanges"
            >
              {{ submitting ? "正在提交…" : "提交修改意见" }}
            </button>
          </template>
          <template v-else>
            <button
              class="secondary-button"
              type="button"
              :disabled="submitting"
              @click="actionMode = 'review'"
            >
              返回
            </button>
            <button
              class="cancel-confirm-button"
              type="button"
              :disabled="submitting"
              @click="emit('cancel')"
            >
              {{ submitting ? "正在终止…" : "确认终止任务" }}
            </button>
          </template>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped src="../../styles/migration-review-dialog.css"></style>
<style scoped src="../../styles/migration-review-content.css"></style>
