import type { MigrationCreatePayload, MigrationTask } from "@/types/migration";

export async function createMigration(
  payload: MigrationCreatePayload,
): Promise<MigrationTask> {
  const response = await fetch("/api/migrations/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("创建迁移任务失败");
  }

  return response.json();
}

export async function getMigration(taskId: number): Promise<MigrationTask> {
  const response = await fetch(`/api/migrations/${taskId}`);

  if (!response.ok) {
    throw new Error("获取迁移任务失败");
  }

  return response.json();
}
