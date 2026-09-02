import asyncio
import json
from pathlib import Path
from typing import Any, Literal

from app.schemas.validation import VueValidationResult

# 当前文件路径：
# backend/app/services/node_runner.py
#
# parents[3] 对应项目根目录：
# react-vue-migrator/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


# Node Runner 执行 pnpm build 后生成的入口文件。
NODE_RUNNER_ENTRY = PROJECT_ROOT / "node-runner" / "dist" / "index.js"


class NodeRunnerError(RuntimeError):
    """Node Runner 调用失败。"""


async def run_node_runner(
    *,
    action: Literal[
        "analyze_react",
        "validate_vue",
    ],
    filename: str,
    source_code: str,
) -> dict[str, Any]:
    """调用 Node Runner 的通用方法。"""

    if not NODE_RUNNER_ENTRY.exists():
        raise NodeRunnerError(
            "没有找到 Node Runner 编译文件："
            f"{NODE_RUNNER_ENTRY}。"
            "请先在 node-runner 目录执行 pnpm build"
        )

    request_data = {
        "action": action,
        "filename": filename,
        "source_code": source_code,
    }

    # 启动：
    # node node-runner/dist/index.js
    process = await asyncio.create_subprocess_exec(
        "node",
        str(NODE_RUNNER_ENTRY),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(
                json.dumps(
                    request_data,
                    ensure_ascii=False,
                ).encode("utf-8")
            ),
            timeout=30,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()

        raise NodeRunnerError(f"Node Runner 执行超时，action={action}") from None

    stderr_text = stderr.decode(
        "utf-8",
        errors="replace",
    )

    if process.returncode != 0:
        raise NodeRunnerError(f"Node Runner 执行失败：{stderr_text or '没有错误信息'}")

    stdout_text = stdout.decode(
        "utf-8",
        errors="replace",
    )

    try:
        result = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        raise NodeRunnerError(
            f"Node Runner 返回的不是合法 JSON。stdout={stdout_text}"
        ) from exc

    if not isinstance(result, dict):
        raise NodeRunnerError("Node Runner 返回结果必须是 JSON 对象")

    return result


async def analyze_react_source(
    *,
    filename: str,
    source_code: str,
) -> dict[str, Any]:
    """调用 Node Runner 分析 React 源代码。"""

    return await run_node_runner(
        action="analyze_react",
        filename=filename,
        source_code=source_code,
    )


async def validate_vue_code(
    *,
    filename: str,
    source_code: str,
) -> VueValidationResult:
    """调用 Node Runner 验证 Vue 源代码。"""

    result = await run_node_runner(
        action="validate_vue",
        filename=filename,
        source_code=source_code,
    )

    # 将 Node 返回的字典转换成 Pydantic 对象。
    return VueValidationResult.model_validate(result)
