from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    database_path: Path = BASE_DIR / "data" / "promptcraft.db"
    generation_model: str = "gpt-4.1-mini"
    admin_ids: frozenset[int] = frozenset()
    support_username: str = ""


def parse_admin_ids(value: str) -> frozenset[int]:
    result: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            admin_id = int(item)
        except ValueError as exc:
            raise RuntimeError(f"Invalid ADMIN_IDS value: {item}") from exc
        if admin_id <= 0:
            raise RuntimeError("ADMIN_IDS must contain positive integers")
        result.add(admin_id)
    return frozenset(result)


def load_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", token),
            ("OPENAI_API_KEY", api_key),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )
    return Settings(
        telegram_bot_token=token,
        openai_api_key=api_key,
        generation_model=os.getenv(
            "OPENAI_GENERATION_MODEL", "gpt-4.1-mini"
        ).strip(),
        admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        support_username=os.getenv("SUPPORT_USERNAME", "").strip().lstrip("@"),
    )
