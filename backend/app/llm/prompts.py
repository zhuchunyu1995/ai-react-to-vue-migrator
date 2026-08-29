# 存放发给大模型的提示词和 Prompt 构造函数。
# 在这个项目中主要包括：
# 生成迁移计划 Prompt
# 生成 Vue 代码 Prompt
# 修复计划 JSON Prompt
# 根据检查错误修复 Vue Prompt
# 它只负责“告诉模型做什么”，不调用数据库、不保存结果。
# 例如
CREATE_PLAN_SYSTEM_PROMPT = """
你是 React 到 Vue 3 的迁移专家。
根据源码分析结果生成迁移计划。
必须遵守给定的结构化输出格式。
"""

GENERATE_VUE_SYSTEM_PROMPT = """
根据用户批准的迁移计划生成 Vue 3 SFC。
使用 <script setup lang="ts">。
不得添加白名单之外的依赖。
"""


def build_repair_prompt(
    code: str,
    errors: list[str],
    approved_plan: str,
) -> str:
    return f"""
    请根据检查错误修复 Vue 代码。

    已批准的计划：
    {approved_plan}

    当前代码：
    {code}

    检查错误：
    {errors}
    """
