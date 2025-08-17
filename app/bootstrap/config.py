import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class AppConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False

    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    database_url: str | None = None
    checkpoint_type: str = "memory"  # Options: memory, postgres
    prompt_root_dir: str = "data/prompts"


def get_config() -> AppConfig:
    return AppConfig(
        debug=os.getenv("DEBUG", "false").lower() == "true",
        reload=os.getenv("RELOAD", "false").lower() == "true",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/agent_template",
        ),
        checkpoint_type=os.getenv("CHECKPOINT_TYPE", "memory"),
        prompt_root_dir=os.getenv("PROMPT_ROOT_DIR", "data/prompts"),
    )
