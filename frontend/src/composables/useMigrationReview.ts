import { ref, type Ref } from "vue";

import { reviewMigration } from "@/api/migration";
import type {
  MigrationPhase,
  MigrationPlan,
  MigrationTask,
} from "@/types/migration";

interface MigrationReviewOptions {
  taskId: Ref<number | null>;
  phase: Ref<MigrationPhase>;
  statusMessage: Ref<string>;
  startPolling: (taskId: number) => void;
  stopPolling: () => void;
}

export function useMigrationReview(options: MigrationReviewOptions) {
  const reviewDialogVisible = ref(false);
  const reviewPlan = ref<MigrationPlan | null>(null);
  const reviewSubmitting = ref(false);
  const reviewError = ref("");

  let lastOpenedPlanKey = "";

  function resetReviewState() {
    reviewDialogVisible.value = false;
    reviewPlan.value = null;
    reviewSubmitting.value = false;
    reviewError.value = "";
    lastOpenedPlanKey = "";
  }

  function handleReviewTask(task: MigrationTask) {
    if (task.status !== "waiting_for_review") return;

    reviewPlan.value = task.migration_plan ?? null;
    if (!reviewPlan.value) return;

    options.stopPolling();

    // 同一任务修改后的计划内容不同，仍然需要再次自动打开审核窗口。
    const planKey = `${task.id}:${JSON.stringify(reviewPlan.value)}`;
    if (lastOpenedPlanKey === planKey) return;

    lastOpenedPlanKey = planKey;
    reviewDialogVisible.value = true;
    reviewError.value = "";
  }

  async function approvePlan(plan: MigrationPlan) {
    const id = options.taskId.value;
    if (!id) return;

    reviewSubmitting.value = true;
    reviewError.value = "";

    try {
      await reviewMigration(id, {
        action: "approve",
        migration_plan: plan,
      });
      reviewDialogVisible.value = false;
      options.phase.value = "generating";
      options.statusMessage.value = "迁移计划已确认，正在生成 Vue 组件。";
      options.startPolling(id);
    } catch (error) {
      reviewError.value = getReviewError(error, "提交审核结果失败");
    } finally {
      reviewSubmitting.value = false;
    }
  }

  async function requestPlanChanges(feedback: string) {
    const id = options.taskId.value;
    if (!id) return;

    reviewSubmitting.value = true;
    reviewError.value = "";

    try {
      await reviewMigration(id, {
        action: "request_changes",
        feedback,
      });
      reviewDialogVisible.value = false;
      options.phase.value = "revision_requested";
      options.statusMessage.value = "修改意见已提交，AI 将重新生成迁移计划。";
      options.startPolling(id);
    } catch (error) {
      reviewError.value = getReviewError(error, "提交修改意见失败");
    } finally {
      reviewSubmitting.value = false;
    }
  }

  async function cancelMigration() {
    const id = options.taskId.value;
    if (!id) return;

    reviewSubmitting.value = true;
    reviewError.value = "";

    try {
      await reviewMigration(id, { action: "cancel" });
      reviewDialogVisible.value = false;
      options.phase.value = "cancelled";
      options.statusMessage.value = "迁移任务已终止，当前源码仍然保留。";
      options.startPolling(id);
    } catch (error) {
      reviewError.value = getReviewError(error, "终止迁移任务失败");
    } finally {
      reviewSubmitting.value = false;
    }
  }

  return {
    reviewDialogVisible,
    reviewPlan,
    reviewSubmitting,
    reviewError,
    resetReviewState,
    handleReviewTask,
    approvePlan,
    requestPlanChanges,
    cancelMigration,
  };
}

function getReviewError(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : `${fallback}，请稍后重试。`;
}
