from __future__ import annotations

import hmac

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from admin_panel.backend.auth import AuthError, create_token, verify_token
from admin_panel.backend.config import load_admin_panel_settings
from admin_panel.backend.database import (
    AdminPanelRepository,
    create_readonly_engine,
)


settings = load_admin_panel_settings()
engine = create_readonly_engine(settings.database_url)
repository = AdminPanelRepository(engine)

app = FastAPI(title="PromptCraftAI Admin Panel API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_token(token, settings.jwt_secret)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not hmac.compare_digest(payload.password, settings.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    return LoginResponse(
        token=create_token(settings.jwt_secret, settings.jwt_ttl_seconds)
    )


@app.get("/api/dashboard")
def dashboard(_admin: dict = Depends(require_admin)) -> dict:
    return repository.dashboard()


@app.get("/api/users")
def users(
    _admin: dict = Depends(require_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None),
    sort: str = Query(default="created_at"),
    direction: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict:
    return repository.users(page, page_size, search, sort, direction)


@app.get("/api/payments")
def payments(
    _admin: dict = Depends(require_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
) -> dict:
    return repository.payments(page, page_size)


@app.get("/api/trials")
def trials(_admin: dict = Depends(require_admin)) -> dict:
    return repository.trials()


@app.get("/api/stats")
def stats(_admin: dict = Depends(require_admin)) -> dict:
    return repository.ai_stats()
