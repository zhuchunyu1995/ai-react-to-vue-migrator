import process from "node:process";

import { analyzeReactSource } from "./analyzer.js";
import type {
  AnalyzeErrorResponse,
  AnalyzeRequest,
  AnalyzeSuccessResponse,
} from "./types.js";

/**
 * 从标准输入 stdin 中读取 Python 传来的 JSON。
 */
async function readStdin(): Promise<string> {
  process.stdin.setEncoding("utf8");

  let input = "";

  for await (const chunk of process.stdin) {
    input += chunk;
  }

  return input;
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
 * Node Runner 主入口。
 *
 * stdout 只能输出最终 JSON，否则 Python 无法正确解析。
 */
async function main(): Promise<void> {
  try {
    const rawInput = await readStdin();
    const parsedInput: unknown = JSON.parse(rawInput);
    const request = validateRequest(parsedInput);

    const analysis = analyzeReactSource(request.filename, request.source_code);

    const response: AnalyzeSuccessResponse = {
      success: true,
      data: analysis,
    };

    process.stdout.write(JSON.stringify(response));
  } catch (error) {
    const response = createErrorResponse(error);

    process.stdout.write(JSON.stringify(response));

    // 非零退出码告诉 Python：本次分析执行失败
    process.exitCode = 1;
  }
}

void main();
