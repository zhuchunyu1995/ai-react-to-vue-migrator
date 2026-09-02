from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """项目配置"""

    deepseek_api_key: SecretStr
    llm_model: str

    llm_base_url: str
    llm_temperature: float = 0.3

    # SQLite 数据库地址
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # LangGraph 持久化检查点数据库，用于 interrupt 后跨请求恢复工作流
    checkpoint_database_path: Path = BASE_DIR / "data/langgraph_checkpoints.db"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
