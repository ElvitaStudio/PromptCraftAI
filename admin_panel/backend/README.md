# PromptCraftAI Admin Panel Backend

Standalone read-only FastAPI backend for the PromptCraftAI admin panel.

Run from the project root:

```bash
pip install -r admin_panel/backend/requirements.txt
uvicorn admin_panel.backend.main:app --reload
```

Configuration:

- `ADMIN_PANEL_PASSWORD` — panel password. Defaults to `admin123` for local
  development only.
- `ADMIN_PANEL_JWT_SECRET` — optional JWT signing secret.
- `ADMIN_PANEL_DATABASE_URL` — optional SQLAlchemy URL. Defaults to the
  existing `data/promptcraft.db` SQLite database.
- `ADMIN_PANEL_CORS_ORIGINS` — optional comma-separated CORS origins.

The backend only reads from the existing database and does not run schema
migrations or alter Telegram bot state.
