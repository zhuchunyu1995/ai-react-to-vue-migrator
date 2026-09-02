import { compileScript, compileTemplate, parse } from "@vue/compiler-sfc";

/**
 * 验证阶段。
 */
export type ValidationStage =
  | "sfc_parse"
  | "script_compile"
  | "template_compile"
  | "migration_rule"
  | "lint"
  | "type_check"
  | "build";
/**
 * 单条验证错误。
 */
export interface ValidationIssue {
  stage: ValidationStage;
  message: string;
  line: number | null;
  column: number | null;
}

/**
 * Vue 代码验证结果。
 */
export interface VueValidationResult {
  success: boolean;
  checks: Record<string, boolean>;
  errors: ValidationIssue[];

  // 保存各个命令的原始输出，方便调试和生成报告。
  details?: Record<string, string>;
}
/**
 * 将 Vue 编译器返回的错误转换成统一格式。
 */
function normalizeError(
  stage: ValidationStage,
  error: unknown,
): ValidationIssue {
  if (typeof error === "string") {
    return {
      stage,
      message: error,
      line: null,
      column: null,
    };
  }

  if (error instanceof Error) {
    const compilerError = error as Error & {
      loc?: {
        line?: number;
        column?: number;
        start?: {
          line?: number;
          column?: number;
        };
      };
    };

    return {
      stage,
      message: compilerError.message,
      line: compilerError.loc?.start?.line ?? compilerError.loc?.line ?? null,
      column:
        compilerError.loc?.start?.column ?? compilerError.loc?.column ?? null,
    };
  }

  return {
    stage,
    message: String(error),
    line: null,
    column: null,
  };
}

/**
 * 校验迁移规则。
 *
 * 这些并不是 Vue 编译错误，而是 React -> Vue 迁移项目
 * 自己定义的业务检查规则。
 */
function validateMigrationRules(sourceCode: string): ValidationIssue[] {
  const errors: ValidationIssue[] = [];

  if (!sourceCode.includes("<script setup")) {
    errors.push({
      stage: "migration_rule",
      message: '必须使用 <script setup lang="ts">',
      line: null,
      column: null,
    });
  }

  if (!sourceCode.includes('lang="ts"')) {
    errors.push({
      stage: "migration_rule",
      message: "script setup 必须启用 TypeScript",
      line: null,
      column: null,
    });
  }

  if (/from\s+["']react["']/.test(sourceCode)) {
    errors.push({
      stage: "migration_rule",
      message: "迁移后的 Vue 代码中仍然存在 React 导入",
      line: null,
      column: null,
    });
  }

  const forbiddenReactApis = [
    "useState(",
    "useEffect(",
    "useMemo(",
    "useCallback(",
    "useRef(",
  ];

  for (const reactApi of forbiddenReactApis) {
    if (sourceCode.includes(reactApi)) {
      errors.push({
        stage: "migration_rule",
        message: `迁移后的代码中仍然存在 React API：${reactApi}`,
        line: null,
        column: null,
      });
    }
  }

  if (sourceCode.includes("className=")) {
    errors.push({
      stage: "migration_rule",
      message: "Vue 模板中不能使用 className，应改为 class",
      line: null,
      column: null,
    });
  }

  return errors;
}

/**
 * 验证一个 Vue 单文件组件。
 */
export function validateVueSfc(
  filename: string,
  sourceCode: string,
): VueValidationResult {
  const errors: ValidationIssue[] = [];

  const checks: Record<string, boolean> = {
    sfc_parse: false,
    script_compile: false,
    template_compile: false,
    migration_rule: false,
  };

  /*
   * 第一步：解析 .vue 单文件组件。
   */
  const parsed = parse(sourceCode, {
    filename,
    sourceMap: false,
  });

  for (const error of parsed.errors) {
    errors.push(normalizeError("sfc_parse", error));
  }

  checks.sfc_parse = parsed.errors.length === 0;

  /*
   * SFC 结构都无法解析时，不继续执行后面的编译检查。
   */
  if (!checks.sfc_parse) {
    return {
      success: false,
      checks,
      errors,
    };
  }

  const descriptor = parsed.descriptor;

  /*
   * 第二步：验证 <script setup>。
   */
  if (!descriptor.scriptSetup) {
    errors.push({
      stage: "script_compile",
      message: "没有找到 <script setup> 代码块",
      line: null,
      column: null,
    });
  } else {
    try {
      compileScript(descriptor, {
        // Vue 编译器要求提供组件唯一 ID。
        id: "migration-validation",
      });

      checks.script_compile = true;
    } catch (error) {
      errors.push(normalizeError("script_compile", error));
    }
  }

  /*
   * 第三步：验证 <template>。
   */
  if (!descriptor.template) {
    errors.push({
      stage: "template_compile",
      message: "没有找到 <template> 代码块",
      line: null,
      column: null,
    });
  } else {
    try {
      const templateResult = compileTemplate({
        id: "migration-validation",
        filename,
        source: descriptor.template.content,
        scoped: descriptor.styles.some((style) => style.scoped),
      });

      for (const error of templateResult.errors) {
        errors.push(normalizeError("template_compile", error));
      }

      checks.template_compile = templateResult.errors.length === 0;
    } catch (error) {
      errors.push(normalizeError("template_compile", error));
    }
  }

  /*
   * 第四步：检查是否残留 React 写法。
   */
  const migrationRuleErrors = validateMigrationRules(sourceCode);

  errors.push(...migrationRuleErrors);

  checks.migration_rule = migrationRuleErrors.length === 0;

  return {
    success: errors.length === 0,
    checks,
    errors,
  };
}
