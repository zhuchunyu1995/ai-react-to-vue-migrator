from functools import lru_cache

from app.core.config import get_settings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


@lru_cache
def get_llm() -> BaseChatModel:
    """获取项目统一使用的大模型实例"""

    settings = get_settings()

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
    )
