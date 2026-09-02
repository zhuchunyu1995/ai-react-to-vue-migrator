import process from "node:process";

import type { AnalyzeErrorResponse, AnalyzeRequest } from "./types.js";

import { analyzeReactSource } from "./analyzer.js";
import { validateVueProject } from "./project-validator.js";

interface RunnerRequest {
  action: "analyze_react" | "validate_vue";
  filename: string;
  source_code: string;
}

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];

  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }

  return Buffer.concat(chunks).toString("utf-8");
}

/**
 * 校验 Python 传入的请求参数。
 */
function validateRequest(value: unknown): AnalyzeRequest {
  if (!value || typeof value !== "object") {
    throw new Error("请求内容必须是 JSON 对象");
  }

  const request = value as Partial<AnalyzeRequest>;

  if (request.action !== "analyze") {
    throw new Error("action 必须为 analyze");
  }

  if (!request.filename || typeof request.filename !== "string") {
    throw new Error("filename 不能为空");
  }

  if (!request.source_code || typeof request.source_code !== "string") {
    throw new Error("source_code 不能为空");
  }

  return request as AnalyzeRequest;
}

/**
 * 将异常转换成结构化错误。
 */
function createErrorResponse(error: unknown): AnalyzeErrorResponse {
  const parsedError = error as Error & {
    code?: string;
    loc?: {
      line: number;
      column: number;
    };
  };

  return {
    success: false,
    error: {
      type: parsedError.code ?? "NODE_RUNNER_ERROR",
      message: parsedError.message ?? "Node Runner 执行失败",
      line: parsedError.loc?.line,
      column: parsedError.loc?.column,
    },
  };
}

/**
 * 读取 Python 后端从 stdin 传入的数据。
 */
async function main(): Promise<void> {
  try {
    const rawInput = await readStdin();
    const request = JSON.parse(rawInput) as RunnerRequest;

    let result: unknown;

    if (request.action === "analyze_react") {
      result = analyzeReactSource(request.filename, request.source_code);
    } else if (request.action === "validate_vue") {
      result = await validateVueProject(request.filename, request.source_code);
    } else {
      throw new Error(`不支持的 action：${request.action}`);
    }

    /*
     * stdout 只能输出最终 JSON。
     * 调试信息应该用 console.error 输出到 stderr。
     */
    process.stdout.write(JSON.stringify(result));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);

    console.error(message);
    process.exitCode = 1;
  }
}

void main();
