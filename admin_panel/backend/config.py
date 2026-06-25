from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class AdminPanelSettings:
    database_url: str
    password: str
    jwt_secret: str
    jwt_ttl_seconds: int = 60 * 60 * 12
    cors_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )


def load_admin_panel_settings() -> AdminPanelSettings:
    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("ADMIN_PANEL_DATABASE_URL", "").strip()
    if not database_url:
        database_path = PROJECT_ROOT / "data" / "promptcraft.db"
        database_url = f"sqlite:///{database_path}"

    password = os.getenv("ADMIN_PANEL_PASSWORD", "").strip() or "admin123"
    jwt_secret = (
        os.getenv("ADMIN_PANEL_JWT_SECRET", "").strip()
        or f"promptcraft-admin-panel:{password}"
    )
    raw_origins = os.getenv("ADMIN_PANEL_CORS_ORIGINS", "").strip()
    cors_origins = (
        tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())
        if raw_origins
        else AdminPanelSettings.__dataclass_fields__["cors_origins"].default
    )
    return AdminPanelSettings(
        database_url=database_url,
        password=password,
        jwt_secret=jwt_secret,
        cors_origins=cors_origins,
    )
