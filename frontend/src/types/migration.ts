/**
 * 后端数据库中的任务状态。
 *
 * queued 是后续建议使用的初始状态。
 */
export type MigrationStatus =
  | "queued"
  | "analyzing"
  | "analyzed"
  | "planning"
  | "planned"
  | "waiting_for_review"
  | "approved"
  | "revision_requested"
  | "revising_plan"
  | "cancelled"
  | "rejected"
  | "generating"
  | "generated"
  | "validating"
  | "validated"
  | "validation_failed"
  | "repairing"
  | "repaired"
  | "report_generated"
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
 * 单条 React → Vue 迁移映射。
 */
export interface MigrationMapping {
  category:
    | "state"
    | "effect"
    | "props"
    | "event"
    | "template"
    | "dependency"
    | "other";
  source: string;
  target: string;
  reason: string;
  source_line: number | null;
  strategy: "rule" | "llm";
  confidence: number;
  needs_review: boolean;
}

/**
 * 等待人工审核的结构化迁移计划。
 */
export interface MigrationPlan {
  component_name: string;
  target_framework: "vue3";
  target_language: "typescript";
  component_style: "script_setup";
  mappings: MigrationMapping[];
  dependencies: string[];
  risks: string[];
  manual_checks: string[];
  generation_constraints: string[];
}

/**
 * 单条 Vue 工具链验证错误。
 */
export interface ValidationIssue {
  stage:
    | "sfc_parse"
    | "script_compile"
    | "template_compile"
    | "migration_rule"
    | "lint"
    | "type_check"
    | "build"
    | "runner";
  message: string;
  line: number | null;
  column: number | null;
}

/**
 * SFC、Lint、Type 和 Build 的完整验证结果。
 */
export interface MigrationValidationResult {
  success: boolean;
  checks: Record<string, boolean>;
  errors: ValidationIssue[];
  details: Record<string, string>;
}

export interface MigrationReportSummary {
  component_name: string;
  source_filename: string;
  generated_filename: string;
  result: string;
  repair_count: number;
}

export interface MigrationReportStatistics {
  mapping_count: number;
  rule_mapping_count: number;
  llm_mapping_count: number;
  needs_review_count: number;
}

/**
 * 后端生成的结构化迁移报告。
 */
export interface MigrationReport {
  version: string;
  generated_at: string;
  summary: MigrationReportSummary;
  statistics: MigrationReportStatistics;
  mappings: MigrationMapping[];
  validation: Omit<MigrationValidationResult, "success"> & { passed: boolean };
  risks: string[];
  manual_checks: string[];
  generation_notes: string[];
  markdown: string;
}

/**
 * POST /api/migrations/{task_id}/review 请求参数。
 */
export type MigrationReviewPayload =
  | {
      action: "approve";
      migration_plan: MigrationPlan;
    }
  | {
      action: "request_changes";
      feedback: string;
    }
  | {
      action: "cancel";
    };

/**
 * POST 创建接口和 GET 查询接口返回的任务结构。
 */
export interface MigrationTask {
  id: number;
  filename: string;
  status: MigrationStatus;
  current_node: string | null;
  created_at: string;
  updated_at?: string | null;
  migration_plan?: MigrationPlan | null;
  approved_plan?: MigrationPlan | null;
  review_feedback?: string | null;
  generated_filename?: string | null;
  generated_code?: string | null;
  generation_notes?: string[] | null;
  validation_passed?: boolean | null;
  validation_result?: MigrationValidationResult | null;
  migration_report?: MigrationReport | null;
}
