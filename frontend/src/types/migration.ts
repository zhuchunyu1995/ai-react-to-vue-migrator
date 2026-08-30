/**
 * 后端数据库中的任务状态。
 *
 * created 是当前数据库模型使用的初始状态。
 * queued 是后续建议使用的初始状态。
 */
export type MigrationStatus =
  | "queued"
  | "analyzing"
  | "planning"
  | "waiting_for_review"
  | "generating"
  | "validating"
  | "repairing"
  | "completed"
  | "failed";

/**
 * 页面状态。
 *
 * idle、submitting 只存在于前端；
 * 其他状态来自后端。
 */
export type MigrationPhase = "idle" | "submitting" | MigrationStatus;

/**
 * 工作流步骤的显示状态。
 */
export type WorkflowStepState = "pending" | "active" | "done" | "error";

/**
 * 迁移目标配置。
 */
export interface MigrationTarget {
  framework: "vue3";
  language: "typescript";
  component_style: "script_setup";
}

/**
 * POST /api/migrations/ 请求参数。
 */
export interface MigrationCreatePayload {
  filename: string;
  source_code: string;
  target: MigrationTarget;
}

/**
 * POST 创建接口和 GET 查询接口返回的任务结构。
 */
export interface MigrationTask {
  id: number;
  filename: string;
  status: MigrationStatus;
  current_node: string | null;
  created_at: string;
}
