from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


TRIAL_AI_REQUEST_LIMIT = 15
SORT_COLUMNS = {
    "created_at": "u.created_at",
    "last_activity": "u.last_active_at",
    "telegram_id": "u.telegram_id",
    "username": "u.username",
    "plan": "u.plan",
    "ai_requests_used": "ai_requests_used",
}


def create_readonly_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False}
        if database_url.startswith("sqlite")
        else {},
        pool_pre_ping=True,
        future=True,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _since_24h() -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()


def _row(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


class AdminPanelRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def dashboard(self) -> dict[str, Any]:
        now = _now()
        since = _since_24h()
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total_users,
                        SUM(CASE WHEN last_active_at >= :since THEN 1 ELSE 0 END)
                            AS active_users_24h,
                        SUM(CASE WHEN plan = 'free' THEN 1 ELSE 0 END)
                            AS free_users,
                        SUM(CASE WHEN plan = 'premium' THEN 1 ELSE 0 END)
                            AS premium_users,
                        SUM(CASE WHEN plan = 'premium_plus' THEN 1 ELSE 0 END)
                            AS premium_plus_users,
                        SUM(CASE WHEN trial_granted = 1 THEN 1 ELSE 0 END)
                            AS trial_users,
                        SUM(
                            CASE
                                WHEN trial_granted = 1
                                 AND trial_expires_at > :now
                                 AND trial_requests_used < :trial_limit
                                THEN 1 ELSE 0
                            END
                        ) AS active_trial_users
                    FROM users
                    """
                ),
                {"since": since, "now": now, "trial_limit": TRIAL_AI_REQUEST_LIMIT},
            ).one()
            payments = connection.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total_payments,
                        COALESCE(SUM(amount), 0) AS total_stars
                    FROM payments
                    WHERE currency = 'XTR'
                    """
                )
            ).one()
            chats = connection.execute(
                text(
                    """
                    SELECT
                        SUM(CASE WHEN assistant = 'gpt' THEN 1 ELSE 0 END)
                            AS total_gpt_chats,
                        SUM(CASE WHEN assistant = 'claude' THEN 1 ELSE 0 END)
                            AS total_claude_chats
                    FROM assistant_chats
                    """
                )
            ).one()
        data = _row(row)
        data.update(_row(payments))
        data.update(_row(chats))
        return {key: int(value or 0) for key, value in data.items()}

    def users(
        self,
        page: int,
        page_size: int,
        search: str | None,
        sort: str,
        direction: str,
    ) -> dict[str, Any]:
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))
        sort_sql = SORT_COLUMNS.get(sort, "u.created_at")
        direction_sql = "ASC" if direction.lower() == "asc" else "DESC"
        where = ""
        params: dict[str, Any] = {
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        if search:
            clean = search.strip().lstrip("@")
            if clean.isdigit():
                where = "WHERE u.telegram_id = :telegram_id"
                params["telegram_id"] = int(clean)
            else:
                where = (
                    "WHERE LOWER(COALESCE(u.username, '')) LIKE LOWER(:search) "
                    "OR LOWER(COALESCE(u.first_name, '')) LIKE LOWER(:search) "
                    "OR LOWER(COALESCE(u.full_name, '')) LIKE LOWER(:search)"
                )
                params["search"] = f"%{clean}%"
        with self.engine.connect() as connection:
            total = connection.execute(
                text(f"SELECT COUNT(*) FROM users u {where}"),
                params,
            ).scalar_one()
            rows = connection.execute(
                text(
                    f"""
                    SELECT
                        u.telegram_id,
                        u.username,
                        u.first_name,
                        u.plan,
                        u.plan_until,
                        u.trial_expires_at AS trial_until,
                        COALESCE(SUM(r.used_count), 0) AS ai_requests_used,
                        u.created_at,
                        u.last_active_at AS last_activity,
                        u.is_blocked
                    FROM users u
                    LEFT JOIN request_usage r ON r.user_id = u.id
                    {where}
                    GROUP BY u.id
                    ORDER BY {sort_sql} {direction_sql}
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            ).fetchall()
        return {
            "items": [
                {
                    **_row(row),
                    "ai_requests_used": int(row.ai_requests_used or 0),
                    "is_blocked": bool(row.is_blocked),
                }
                for row in rows
            ],
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "total_pages": max(1, (int(total) + page_size - 1) // page_size),
        }

    def payments(self, page: int, page_size: int) -> dict[str, Any]:
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))
        params = {"limit": page_size, "offset": (page - 1) * page_size}
        with self.engine.connect() as connection:
            total = connection.execute(text("SELECT COUNT(*) FROM payments")).scalar_one()
            rows = connection.execute(
                text(
                    """
                    SELECT
                        p.user_id,
                        p.plan AS tariff,
                        p.amount AS stars,
                        p.telegram_payment_charge_id AS charge_id,
                        p.created_at AS payment_date
                    FROM payments p
                    ORDER BY p.created_at DESC, p.id DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            ).fetchall()
        return {
            "items": [_row(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "total_pages": max(1, (int(total) + page_size - 1) // page_size),
        }

    def trials(self) -> dict[str, list[dict[str, Any]]]:
        now = _now()
        with self.engine.connect() as connection:
            active = connection.execute(
                text(
                    """
                    SELECT telegram_id, username, first_name, trial_expires_at,
                           trial_requests_used
                    FROM users
                    WHERE trial_granted = 1
                      AND trial_expires_at > :now
                      AND trial_requests_used < :trial_limit
                    ORDER BY trial_expires_at ASC
                    """
                ),
                {"now": now, "trial_limit": TRIAL_AI_REQUEST_LIMIT},
            ).fetchall()
            expired = connection.execute(
                text(
                    """
                    SELECT telegram_id, username, first_name, trial_expires_at,
                           trial_requests_used
                    FROM users
                    WHERE trial_granted = 1
                      AND (
                        trial_expires_at <= :now
                        OR trial_requests_used >= :trial_limit
                      )
                    ORDER BY trial_expires_at DESC
                    """
                ),
                {"now": now, "trial_limit": TRIAL_AI_REQUEST_LIMIT},
            ).fetchall()
        return {
            "active": [_row(row) for row in active],
            "expired": [_row(row) for row in expired],
        }

    def ai_stats(self) -> dict[str, Any]:
        with self.engine.connect() as connection:
            prompt_stats = connection.execute(
                text(
                    """
                    SELECT
                        SUM(
                            CASE
                                WHEN target_ai IN ('chatgpt', 'gpt_image')
                                THEN 1 ELSE 0
                            END
                        ) AS prompt_gpt,
                        SUM(
                            CASE
                                WHEN target_ai LIKE 'claude%'
                                THEN 1 ELSE 0
                            END
                        ) AS prompt_claude,
                        COUNT(*) AS prompt_total
                    FROM prompts
                    """
                )
            ).one()
            assistant_stats = connection.execute(
                text(
                    """
                    SELECT
                        SUM(
                            CASE
                                WHEN c.assistant = 'gpt' AND m.role = 'user'
                                THEN 1 ELSE 0
                            END
                        ) AS assistant_gpt,
                        SUM(
                            CASE
                                WHEN c.assistant = 'claude' AND m.role = 'user'
                                THEN 1 ELSE 0
                            END
                        ) AS assistant_claude
                    FROM assistant_messages m
                    JOIN assistant_chats c ON c.id = m.chat_id
                    """
                )
            ).one()
            users = connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
        gpt_requests = int(prompt_stats.prompt_gpt or 0) + int(
            assistant_stats.assistant_gpt or 0
        )
        claude_requests = int(prompt_stats.prompt_claude or 0) + int(
            assistant_stats.assistant_claude or 0
        )
        total_ai_requests = gpt_requests + claude_requests
        average = total_ai_requests / int(users or 1)
        return {
            "gpt_requests": gpt_requests,
            "claude_requests": claude_requests,
            "total_ai_requests": total_ai_requests,
            "average_requests_per_user": round(average, 2),
        }
