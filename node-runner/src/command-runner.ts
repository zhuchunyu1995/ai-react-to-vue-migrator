import { spawn } from "node:child_process";

export interface CommandResult {
  success: boolean;
  exitCode: number | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
  durationMs: number;
}

/**
 * 执行 pnpm 子命令。
 */
export function runPnpmCommand(
  args: string[],
  cwd: string,
  timeoutMs = 60_000,
): Promise<CommandResult> {
  return new Promise((resolve, reject) => {
    const startedAt = Date.now();

    const command = process.platform === "win32" ? "pnpm.cmd" : "pnpm";

    const child = spawn(command, args, {
      cwd,
      env: {
        ...process.env,

        FORCE_COLOR: "0",
        NO_COLOR: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    let timedOut = false;

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf-8");
    });

    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf-8");
    });

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGKILL");
    }, timeoutMs);

    child.once("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });

    child.once("close", (exitCode) => {
      clearTimeout(timer);

      resolve({
        success: exitCode === 0 && !timedOut,
        exitCode,
        stdout,
        stderr,
        timedOut,
        durationMs: Date.now() - startedAt,
      });
    });
  });
}
