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
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    oauth_server_port: int
    subscription_stars_amount: int
    free_trial_days: int
    whisper_url: str

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
            google_client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            google_redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8443/oauth/callback"),
            oauth_server_port=int(os.environ.get("OAUTH_SERVER_PORT", "8443")),
            subscription_stars_amount=int(os.environ.get("DABBAR_STARS_AMOUNT", "10000")),
            free_trial_days=int(os.environ.get("DABBAR_FREE_TRIAL_DAYS", "7")),
            whisper_url=os.environ.get("WHISPER_URL", "http://localhost:9000"),
        )


CONFIG = Config.load() if os.environ.get("DABBAR_SKIP_CONFIG") != "1" else None
