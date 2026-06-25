# PromptCraftAI Admin Panel

Standalone read-only admin panel for PromptCraftAI.

The panel is intentionally isolated from the Telegram bot runtime:

- it does not modify `.env`;
- it reads the existing SQLite database;
- it does not run migrations;
- it does not change Telegram Stars payments, Trial, Premium Plus, GPT Assistant, or Claude Assistant logic.

## Backend

```bash
pip install -r admin_panel/backend/requirements.txt
uvicorn admin_panel.backend.main:app --reload
```

Default API URL: `http://127.0.0.1:8000`

Authentication uses `ADMIN_PANEL_PASSWORD`. If the variable is absent, the development fallback is `admin123`.

Optional environment variables:

- `ADMIN_PANEL_PASSWORD`
- `ADMIN_PANEL_JWT_SECRET`
- `ADMIN_PANEL_DATABASE_URL`
- `ADMIN_PANEL_CORS_ORIGINS`

## Frontend

```bash
cd admin_panel/frontend
npm install
npm run dev
```

Default frontend URL: `http://localhost:3000`

If the backend runs on another URL:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

