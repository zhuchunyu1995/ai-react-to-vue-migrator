import { onBeforeUnmount, ref } from "vue";

import { getMigration } from "@/api/migration";
import type { MigrationTask } from "@/types/migration";

const POLLING_INTERVAL = 2000;

const STOP_STATUSES = ["rejected", "cancelled", "completed", "failed"];

export function useMigrationPolling() {
  const task = ref<MigrationTask | null>(null);
  const pollingError = ref<string | null>(null);
  const isPolling = ref(false);

  let pollingTimer: ReturnType<typeof setTimeout> | null = null;

  const stopPolling = () => {
    isPolling.value = false;

    if (pollingTimer) {
      clearTimeout(pollingTimer);
      pollingTimer = null;
    }
  };

  const poll = async (taskId: number) => {
    if (!isPolling.value) {
      return;
    }

    try {
      task.value = await getMigration(taskId);
      pollingError.value = null;

      const planIsReady =
        task.value.status === "waiting_for_review" &&
        task.value.migration_plan !== null &&
        task.value.migration_plan !== undefined;

      if (STOP_STATUSES.includes(task.value.status) || planIsReady) {
        stopPolling();
        return;
      }
    } catch (error) {
      pollingError.value =
        error instanceof Error ? error.message : "查询状态失败";
    }

    if (isPolling.value) {
      pollingTimer = setTimeout(() => poll(taskId), POLLING_INTERVAL);
    }
  };

  const startPolling = (taskId: number) => {
    stopPolling();
    isPolling.value = true;

    void poll(taskId);
  };

  const resetPolling = () => {
    stopPolling();
    task.value = null;
    pollingError.value = null;
  };

  onBeforeUnmount(() => {
    stopPolling();
  });

  return {
    task,
    isPolling,
    pollingError,
    startPolling,
    stopPolling,
    resetPolling,
  };
}
