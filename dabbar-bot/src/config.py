"""Dabbar bot configuration loaded from environment."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    telegram_token: str
    ollama_host: str
    model_main: str
    model_fast: str
    data_dir: Path
    timezone: str
    admin_id: int | None

    @classmethod
    def load(cls) -> "Config":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

        data_dir = Path(os.environ.get("DABBAR_DATA_DIR", "./data"))
        data_dir.mkdir(parents=True, exist_ok=True)

        admin_raw = os.environ.get("DABBAR_ADMIN_ID", "").strip()
        admin_id = int(admin_raw) if admin_raw.isdigit() else None

        return cls(
            telegram_token=token,
            ollama_host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            model_main=os.environ.get("OLLAMA_MODEL_MAIN", "llama3.1:8b"),
            model_fast=os.environ.get("OLLAMA_MODEL_FAST", "qwen2.5:3b"),
            data_dir=data_dir,
            timezone=os.environ.get("DABBAR_TIMEZONE", "Asia/Dubai"),
            admin_id=admin_id,
        )


CONFIG = Config.load() if os.environ.get("DABBAR_SKIP_CONFIG") != "1" else None
