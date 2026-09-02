import { copyFile, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";

import { dirname, join, resolve } from "node:path";

import { fileURLToPath } from "node:url";

import { runPnpmCommand, type CommandResult } from "./command-runner.js";

import {
  validateVueSfc,
  type ValidationIssue,
  type VueValidationResult,
} from "./validator.js";

/*
 * 当前编译后文件位于：
 * node-runner/dist/project-validator.js
 */
const CURRENT_DIRECTORY = dirname(fileURLToPath(import.meta.url));

/*
 * Node Runner 根目录。
 */
const NODE_RUNNER_ROOT = resolve(CURRENT_DIRECTORY, "..");

/*
 * 固定验证项目模板。
 */
const TEMPLATE_DIRECTORY = join(NODE_RUNNER_ROOT, "validation-template");

/*
 * 每次验证创建的临时工作区根目录。
 */
const WORKSPACES_DIRECTORY = join(NODE_RUNNER_ROOT, ".validation-workspaces");

/*
 * ESLint 配置文件。
 */
const ESLINT_CONFIG = join(NODE_RUNNER_ROOT, "eslint.config.mjs");

/**
 * 创建一个完整的临时 Vue 验证项目。
 */
async function createValidationWorkspace(workspace: string): Promise<void> {
  const workspaceSourceDirectory = join(workspace, "src");

  /*
   * mkdtemp 只会创建任务根目录，
   * 所以这里必须单独创建 src。
   */
  await mkdir(workspaceSourceDirectory, {
    recursive: true,
  });

  /*
   * 显式复制模板文件。
   *
   * 不直接复制整个目录，
   * 避免不同环境下产生额外目录层级。
   */
  await Promise.all([
    copyFile(
      join(TEMPLATE_DIRECTORY, "package.json"),
      join(workspace, "package.json"),
    ),

    copyFile(
      join(TEMPLATE_DIRECTORY, "tsconfig.json"),
      join(workspace, "tsconfig.json"),
    ),

    copyFile(
      join(TEMPLATE_DIRECTORY, "vite.config.ts"),
      join(workspace, "vite.config.ts"),
    ),

    copyFile(
      join(TEMPLATE_DIRECTORY, "src", "index.ts"),
      join(workspaceSourceDirectory, "index.ts"),
    ),
  ]);
}

/**
 * 限制命令输出长度。
 *
 * 防止 ESLint、vue-tsc 或 Vite 输出过长，
 * 导致 LangGraph State 和数据库数据过大。
 */
function limitOutput(value: string, maximumLength = 12_000): string {
  const trimmedValue = value.trim();

  if (trimmedValue.length <= maximumLength) {
    return trimmedValue;
  }

  return trimmedValue.slice(0, maximumLength) + "\n...输出已截断";
}

/**
 * 合并命令的标准输出和错误输出。
 */
function getCommandOutput(result: CommandResult): string {
  const output = [result.stdout, result.stderr].filter(Boolean).join("\n");

  if (result.timedOut) {
    return "命令执行超时\n" + limitOutput(output);
  }

  return limitOutput(output);
}

/**
 * 解析 ESLint 返回的 JSON。
 */
function parseLintErrors(result: CommandResult): ValidationIssue[] {
  if (result.success) {
    return [];
  }

  try {
    const files = JSON.parse(result.stdout) as Array<{
      filePath?: string;

      messages: Array<{
        message: string;
        ruleId: string | null;
        line?: number;
        column?: number;
      }>;
    }>;

    const errors = files.flatMap((file) => {
      return file.messages.map((message) => {
        const ruleDescription = message.ruleId ? ` (${message.ruleId})` : "";

        return {
          stage: "lint" as const,
          message: message.message + ruleDescription,
          line: message.line ?? null,
          column: message.column ?? null,
        };
      });
    });

    if (errors.length > 0) {
      return errors;
    }
  } catch {
    /*
     * 如果 stdout 不是合法的 ESLint JSON，
     * 继续返回原始命令输出。
     */
  }

  return [
    {
      stage: "lint",
      message: getCommandOutput(result) || "ESLint 执行失败",
      line: null,
      column: null,
    },
  ];
}

/**
 * 解析 vue-tsc 类型检查错误。
 */
function parseTypeErrors(result: CommandResult): ValidationIssue[] {
  if (result.success) {
    return [];
  }

  const output = getCommandOutput(result);
  const errors: ValidationIssue[] = [];

  /*
   * 常见 vue-tsc 错误格式：
   *
   * src/Test.vue(3,7): error TS2322:
   * Type 'number' is not assignable to type 'string'.
   */
  for (const outputLine of output.split("\n")) {
    const match = outputLine.match(
      /\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)/,
    );

    if (!match) {
      continue;
    }

    const line = Number(match[1]);
    const column = Number(match[2]);
    const errorCode = match[3];
    const errorMessage = match[4];

    errors.push({
      stage: "type_check",
      message: `${errorCode}: ${errorMessage}`,
      line,
      column,
    });
  }

  if (errors.length > 0) {
    return errors;
  }

  return [
    {
      stage: "type_check",
      message: output || "vue-tsc 类型检查失败",
      line: null,
      column: null,
    },
  ];
}

/**
 * 解析 Vite Build 错误。
 */
function parseBuildErrors(result: CommandResult): ValidationIssue[] {
  if (result.success) {
    return [];
  }

  return [
    {
      stage: "build",
      message: getCommandOutput(result) || "Vite Build 执行失败",
      line: null,
      column: null,
    },
  ];
}

/**
 * 对大模型生成的 Vue 组件执行完整验证。
 *
 * 验证顺序：
 *
 * 1. Vue SFC 编译
 * 2. ESLint
 * 3. vue-tsc 类型检查
 * 4. Vite Build
 */
export async function validateVueProject(
  filename: string,
  sourceCode: string,
): Promise<VueValidationResult> {
  /*
   * 第一步：执行内存级 SFC 验证。
   */
  const sfcResult = validateVueSfc(filename, sourceCode);

  const checks: Record<string, boolean> = {
    ...sfcResult.checks,
    lint: false,
    type_check: false,
    build: false,
  };

  /*
   * SFC 无法解析时，没有必要继续执行后面的命令。
   */
  if (!sfcResult.success) {
    return {
      success: false,
      checks,
      errors: sfcResult.errors,
      details: {
        lint: "跳过：SFC 验证未通过",
        type_check: "跳过：SFC 验证未通过",
        build: "跳过：SFC 验证未通过",
      },
    };
  }

  /*
   * 创建临时工作区根目录。
   */
  await mkdir(WORKSPACES_DIRECTORY, {
    recursive: true,
  });

  /*
   * 创建本次任务的独立临时目录。
   *
   * 例如：
   * .validation-workspaces/task-AbCd12
   */
  const workspace = await mkdtemp(join(WORKSPACES_DIRECTORY, "task-"));

  try {
    /*
     * 创建临时 Vue 验证项目。
     */
    await createValidationWorkspace(workspace);

    const generatedComponentPath = join(
      workspace,
      "src",
      "GeneratedComponent.vue",
    );

    /*
     * 将大模型生成的 Vue 代码写入临时项目。
     */
    await writeFile(generatedComponentPath, sourceCode, "utf-8");

    /*
     * 第二步：执行 ESLint。
     */
    const lintResult = await runPnpmCommand(
      [
        "exec",
        "eslint",
        "--config",
        ESLINT_CONFIG,
        "--format",
        "json",
        generatedComponentPath,
      ],
      NODE_RUNNER_ROOT,
      30_000,
    );

    checks.lint = lintResult.success;

    /*
     * 第三步：执行 vue-tsc 类型检查。
     */
    const typeResult = await runPnpmCommand(
      [
        "exec",
        "vue-tsc",
        "--noEmit",
        "--project",
        join(workspace, "tsconfig.json"),
      ],
      NODE_RUNNER_ROOT,
      60_000,
    );

    checks.type_check = typeResult.success;

    /*
     * 第四步：执行 Vite 生产构建。
     */
    const buildResult = await runPnpmCommand(
      [
        "exec",
        "vite",
        "build",
        workspace,
        "--config",
        join(workspace, "vite.config.ts"),
      ],
      NODE_RUNNER_ROOT,
      60_000,
    );

    checks.build = buildResult.success;

    /*
     * 合并全部错误。
     */
    const errors: ValidationIssue[] = [
      ...sfcResult.errors,
      ...parseLintErrors(lintResult),
      ...parseTypeErrors(typeResult),
      ...parseBuildErrors(buildResult),
    ];

    /*
     * 四项全部通过才算验证成功。
     */
    const success =
      sfcResult.success &&
      lintResult.success &&
      typeResult.success &&
      buildResult.success;

    return {
      success,
      checks,
      errors,

      details: {
        lint: lintResult.success
          ? "ESLint 检查通过"
          : getCommandOutput(lintResult),

        type_check: typeResult.success
          ? "vue-tsc 类型检查通过"
          : getCommandOutput(typeResult),

        build: buildResult.success
          ? "Vite Build 构建通过"
          : getCommandOutput(buildResult),
      },
    };
  } finally {
    /*
     * 无论成功、失败或者抛出异常，
     * 都清理本次任务的临时目录。
     */
    await rm(workspace, {
      recursive: true,
      force: true,
    });
  }
}
