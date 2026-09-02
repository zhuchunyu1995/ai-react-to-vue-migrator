import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.schemas.source_analysis import SourceAnalysis

# 当前文件位置：
# backend/app/integrations/node_runner.py
#
# parents[3] 对应项目根目录：
# react-vue-migrator/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# TypeScript 编译后的 Node Runner 入口
NODE_RUNNER_ENTRY = PROJECT_ROOT / "node-runner" / "dist" / "index.js"


class NodeRunnerError(RuntimeError):
    """Node Runner 调用失败。"""


class NodeRunnerClient:
    """负责 Python 与 Node Runner 之间的通信。"""

    def __init__(
        self,
        entry_path: Path = NODE_RUNNER_ENTRY,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.entry_path = entry_path
        self.timeout_seconds = timeout_seconds

    async def analyze(
        self,
        filename: str,
        source_code: str,
    ) -> SourceAnalysis:
        """调用 Node Runner 分析 React 源码。"""

        if not self.entry_path.exists():
            raise NodeRunnerError(
                f"找不到 Node Runner：{self.entry_path}，"
                "请先进入 node-runner 执行 pnpm build"
            )

        request_data = {
            "action": "analyze",
            "filename": filename,
            "source_code": source_code,
        }

        try:
            process = await asyncio.create_subprocess_exec(
                "node",
                str(self.entry_path),
                # Python 通过 stdin 向 Node 发送 JSON
                stdin=asyncio.subprocess.PIPE,
                # 可以读取console.log输出的结果
                stdout=asyncio.subprocess.PIPE,
                # stderr 用来接收运行时错误
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise NodeRunnerError("没有找到 node 命令，请确认 Node.js 已安装") from exc

        request_bytes = json.dumps(
            request_data,
            ensure_ascii=False,
        ).encode("utf-8")

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(request_bytes),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            # 超时后终止 Node 子进程，避免残留进程
            process.kill()
            await process.wait()

            raise NodeRunnerError(
                f"Node Runner 执行超过 {self.timeout_seconds} 秒"
            ) from exc

        stdout_text = stdout.decode("utf-8").strip()
        stderr_text = stderr.decode("utf-8").strip()

        if not stdout_text:
            raise NodeRunnerError(
                f"Node Runner 没有返回结果：{stderr_text or '未知错误'}"
            )

        try:
            response: dict[str, Any] = json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            raise NodeRunnerError(
                f"Node Runner 返回了非法 JSON：{stdout_text}"
            ) from exc

        if not response.get("success"):
            error = response.get("error", {})
            message = error.get("message", "Node Runner 分析失败")
            line = error.get("line")
            column = error.get("column")

            location = ""

            if line is not None:
                location = f"，位置：第 {line} 行"

                if column is not None:
                    location += f"第 {column} 列"

            raise NodeRunnerError(f"{message}{location}")

        # 即使 success 为 true，也检查 Node 进程是否异常退出
        if process.returncode != 0:
            raise NodeRunnerError(stderr_text or "Node Runner 异常退出")

        try:
            # 使用 Pydantic 校验 Node 返回的数据结构
            return SourceAnalysis.model_validate(response["data"])
        except (KeyError, ValidationError) as exc:
            raise NodeRunnerError("Node Runner 返回的数据结构不符合要求") from exc


# 创建一个可以复用的客户端实例
node_runner_client = NodeRunnerClient()
