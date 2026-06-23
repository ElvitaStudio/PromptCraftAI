from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite

from app.plans import (
    FREE,
    PREMIUM,
    PREMIUM_PLUS,
    PRO,
    VALID_PLANS,
    get_plan_limits,
    TRIAL_AI_REQUEST_LIMIT,
    TRIAL_DURATION_HOURS,
)
from app.prompt_profiles import (
    DIFFICULTIES,
    EXPORT_FORMATS,
    RESPONSE_STYLES,
    WORKFLOWS,
    validate_profile,
)


@dataclass(frozen=True, slots=True)
class User:
    id: int
    telegram_id: int
    plan: str
    language: str | None = None
    referred_by: int | None = None
    premium_until: str | None = None
    plan_until: str | None = None
    is_blocked: bool = False
    last_category: str = "text"
    last_target_ai: str = "chatgpt"
    last_difficulty: str = "simple"
    last_response_style: str = "professional"
    last_workflow: str = "create"
    export_format: str = "txt"
    trial_granted: bool = False
    trial_started_at: str | None = None
    trial_expires_at: str | None = None
    trial_requests_used: int = 0
    trial_notification_sent: bool = False

    @property
    def trial_active(self) -> bool:
        if (
            not self.trial_granted
            or not self.trial_expires_at
            or self.trial_requests_used >= TRIAL_AI_REQUEST_LIMIT
        ):
            return False
        try:
            expires = datetime.fromisoformat(self.trial_expires_at)
        except ValueError:
            return False
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > datetime.now(timezone.utc)

    @property
    def trial_remaining(self) -> int:
        return max(
            0,
            TRIAL_AI_REQUEST_LIMIT - self.trial_requests_used,
        )

    @property
    def entitlement_plan(self) -> str:
        return PREMIUM_PLUS if self.trial_active else self.plan


@dataclass(frozen=True, slots=True)
class Usage:
    used: int
    limit: int | None

    @property
    def remaining(self) -> int | None:
        return None if self.limit is None else max(0, self.limit - self.used)


@dataclass(frozen=True, slots=True)
class PromptRecord:
    id: int
    user_id: int
    category: str
    target_ai: str
    source_text: str
    prompt_text: str
    mode: str
    created_at: str
    language: str = "ru"


@dataclass(frozen=True, slots=True)
class PromptHistoryPage:
    prompts: list[PromptRecord]
    page: int
    total_prompts: int
    total_pages: int


@dataclass(frozen=True, slots=True)
class Favorite:
    id: int
    user_id: int
    prompt_id: int
    title: str
    created_at: str
    prompt: PromptRecord


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    user: User
    created: bool
    referral_rewarded: bool


@dataclass(frozen=True, slots=True)
class TrialActivation:
    user: User
    activated_now: bool
    notification_required: bool


@dataclass(frozen=True, slots=True)
class AIRequestReservation:
    allowed: bool
    source: str | None = None


@dataclass(frozen=True, slots=True)
class Payment:
    id: int
    user_id: int
    plan: str
    currency: str
    amount: int
    payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class NewsItem:
    id: int
    title: str
    text: str
    language: str
    created_at: str


@dataclass(frozen=True, slots=True)
class BroadcastRecipient:
    user_id: int
    telegram_id: int
    plan: str
    language: str


@dataclass(frozen=True, slots=True)
class AssistantChat:
    id: int
    user_id: int
    assistant: str
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class AssistantMessage:
    id: int
    chat_id: int
    role: str
    content: str
    created_at: str


@dataclass(frozen=True, slots=True)
class AdminUser:
    user_id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    full_name: str | None
    language: str | None
    plan: str
    plan_until: str | None
    premium_until: str | None
    is_blocked: bool
    created_at: str
    requests_today: int = 0
    prompts_total: int = 0
    referrals_count: int = 0

    @property
    def display_name(self) -> str:
        if self.full_name:
            return self.full_name
        return " ".join(
            part for part in (self.first_name, self.last_name) if part
        ) or "—"


@dataclass(frozen=True, slots=True)
class AdminUserPage:
    users: list[AdminUser]
    page: int
    total_users: int
    total_pages: int


@dataclass(frozen=True, slots=True)
class AdminStatistics:
    total_users: int
    free_users: int
    pro_users: int
    premium_users: int
    new_users_24h: int
    revenue_stars: int
    pro_sales: int
    premium_sales: int
    prompts_total: int
    prompts_today: int
    premium_plus_users: int = 0
    premium_plus_sales: int = 0


@dataclass(frozen=True, slots=True)
class AdminReferrer:
    display_name: str
    username: str | None
    invited_count: int


@dataclass(frozen=True, slots=True)
class AdminReferral:
    inviter_name: str
    inviter_username: str | None
    invited_name: str
    invited_username: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class AdminReferralReport:
    total_referrals: int
    top_referrers: list[AdminReferrer]
    referrals: list[AdminReferral]


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with self._connect() as db:
            await db.executescript(
                """
                PRAGMA journal_mode = WAL;
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT, first_name TEXT, last_name TEXT,
                    full_name TEXT, language TEXT,
                    plan TEXT NOT NULL DEFAULT 'free', plan_until TEXT,
                    referred_by INTEGER, premium_until TEXT,
                    is_blocked INTEGER NOT NULL DEFAULT 0,
                    last_active_at TEXT,
                    last_category TEXT NOT NULL DEFAULT 'text',
                    last_target_ai TEXT NOT NULL DEFAULT 'chatgpt',
                    last_difficulty TEXT NOT NULL DEFAULT 'simple',
                    last_response_style TEXT NOT NULL DEFAULT 'professional',
                    last_workflow TEXT NOT NULL DEFAULT 'create',
                    export_format TEXT NOT NULL DEFAULT 'txt',
                    trial_granted INTEGER NOT NULL DEFAULT 0,
                    trial_started_at TEXT,
                    trial_expires_at TEXT,
                    trial_requests_used INTEGER NOT NULL DEFAULT 0,
                    trial_notification_sent INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    FOREIGN KEY (referred_by) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS request_usage (
                    user_id INTEGER NOT NULL, usage_date TEXT NOT NULL,
                    used_count INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, usage_date),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS improvement_usage (
                    user_id INTEGER NOT NULL, usage_date TEXT NOT NULL,
                    used_count INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, usage_date),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL, category TEXT NOT NULL,
                    target_ai TEXT NOT NULL, source_text TEXT NOT NULL,
                    prompt_text TEXT NOT NULL, mode TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'ru',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_prompts_user_created
                    ON prompts(user_id, created_at);
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prompt_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, prompt_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_favorites_user_created
                    ON favorites(user_id, created_at);
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id INTEGER NOT NULL, invited_id INTEGER NOT NULL UNIQUE,
                    reward_days INTEGER NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY (inviter_id) REFERENCES users(id),
                    FOREIGN KEY (invited_id) REFERENCES users(id),
                    CHECK (inviter_id != invited_id)
                );
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL, plan TEXT NOT NULL,
                    currency TEXT NOT NULL, amount INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    telegram_payment_charge_id TEXT NOT NULL UNIQUE,
                    provider_payment_charge_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_news_language_created
                    ON news(language, created_at);
                CREATE TABLE IF NOT EXISTS assistant_chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    assistant TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_assistant_chats_user_model
                    ON assistant_chats(user_id, assistant, updated_at);
                CREATE TABLE IF NOT EXISTS assistant_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES assistant_chats(id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_assistant_messages_chat
                    ON assistant_messages(chat_id, id);
                """
            )
            prompt_columns = {
                row[1]
                for row in await (
                    await db.execute("PRAGMA table_info(prompts)")
                ).fetchall()
            }
            if "language" not in prompt_columns:
                await db.execute(
                    "ALTER TABLE prompts ADD COLUMN "
                    "language TEXT NOT NULL DEFAULT 'ru'"
                )
            user_columns = {
                row[1]
                for row in await (
                    await db.execute("PRAGMA table_info(users)")
                ).fetchall()
            }
            preference_columns = {
                "is_blocked": "INTEGER NOT NULL DEFAULT 0",
                "last_category": "TEXT NOT NULL DEFAULT 'text'",
                "last_target_ai": "TEXT NOT NULL DEFAULT 'chatgpt'",
                "last_difficulty": "TEXT NOT NULL DEFAULT 'simple'",
                "last_response_style": (
                    "TEXT NOT NULL DEFAULT 'professional'"
                ),
                "last_workflow": "TEXT NOT NULL DEFAULT 'create'",
                "export_format": "TEXT NOT NULL DEFAULT 'txt'",
                "last_active_at": "TEXT",
                "trial_granted": "INTEGER NOT NULL DEFAULT 0",
                "trial_started_at": "TEXT",
                "trial_expires_at": "TEXT",
                "trial_requests_used": "INTEGER NOT NULL DEFAULT 0",
                "trial_notification_sent": "INTEGER NOT NULL DEFAULT 0",
            }
            for name, definition in preference_columns.items():
                if name not in user_columns:
                    await db.execute(
                        f"ALTER TABLE users ADD COLUMN {name} {definition}"
                    )
            await db.commit()

    @asynccontextmanager
    async def _connect(self) -> AsyncIterator[aiosqlite.Connection]:
        db = await aiosqlite.connect(self.path, timeout=30)
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            yield db
        finally:
            await db.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    @staticmethod
    def _is_future(value: str | None) -> bool:
        if not value:
            return False
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return False
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed > datetime.now(timezone.utc)

    @staticmethod
    def _extend_until(value: str | None, days: int) -> str:
        now = datetime.now(timezone.utc)
        base = now
        if value:
            try:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if parsed > now:
                    base = parsed
            except ValueError:
                pass
        return (base + timedelta(days=days)).isoformat()

    def _row_to_user(self, row: aiosqlite.Row) -> User:
        plan = row["plan"] if row["plan"] in VALID_PLANS else FREE
        if self._is_future(row["premium_until"]):
            plan = PREMIUM
        elif row["plan_until"] and not self._is_future(row["plan_until"]):
            plan = FREE
        return User(
            id=row["id"], telegram_id=row["telegram_id"], plan=plan,
            language=row["language"], referred_by=row["referred_by"],
            premium_until=row["premium_until"], plan_until=row["plan_until"],
            is_blocked=bool(row["is_blocked"]),
            last_category=row["last_category"],
            last_target_ai=row["last_target_ai"],
            last_difficulty=row["last_difficulty"],
            last_response_style=row["last_response_style"],
            last_workflow=row["last_workflow"],
            export_format=row["export_format"],
            trial_granted=bool(row["trial_granted"]),
            trial_started_at=row["trial_started_at"],
            trial_expires_at=row["trial_expires_at"],
            trial_requests_used=int(row["trial_requests_used"]),
            trial_notification_sent=bool(row["trial_notification_sent"]),
        )

    async def register_user(
        self, telegram_id: int, username: str | None,
        first_name: str | None, referred_by_telegram_id: int | None = None,
        reward_days: int = 3, last_name: str | None = None,
        full_name: str | None = None,
    ) -> RegistrationResult:
        now = self._now()
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")
            row = await (
                await db.execute(
                    "SELECT * FROM users WHERE telegram_id=?", (telegram_id,)
                )
            ).fetchone()
            if row:
                await db.execute(
                    "UPDATE users SET username=?, first_name=?, last_name=?, "
                    "full_name=?, last_active_at=?, updated_at=? WHERE id=?",
                    (
                        username, first_name, last_name, full_name,
                        now, now, row["id"],
                    ),
                )
                row = await (
                    await db.execute(
                        "SELECT * FROM users WHERE id=?", (row["id"],)
                    )
                ).fetchone()
                await db.commit()
                return RegistrationResult(
                    self._row_to_user(row), False, False
                )
            cursor = await db.execute(
                "INSERT INTO users (telegram_id, username, first_name, "
                "last_name, full_name, plan, last_active_at, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, 'free', ?, ?, ?)",
                (
                    telegram_id, username, first_name, last_name,
                    full_name, now, now, now,
                ),
            )
            user_id = int(cursor.lastrowid)
            rewarded = False
            if referred_by_telegram_id and referred_by_telegram_id != telegram_id:
                inviter = await (
                    await db.execute(
                        "SELECT id, premium_until FROM users WHERE telegram_id=?",
                        (referred_by_telegram_id,),
                    )
                ).fetchone()
                if inviter:
                    inserted = await db.execute(
                        "INSERT OR IGNORE INTO referrals "
                        "(inviter_id, invited_id, reward_days, created_at) "
                        "VALUES (?, ?, ?, ?)",
                        (inviter["id"], user_id, reward_days, now),
                    )
                    if inserted.rowcount == 1:
                        until = self._extend_until(
                            inviter["premium_until"], reward_days
                        )
                        await db.execute(
                            "UPDATE users SET premium_until=?, updated_at=? "
                            "WHERE id=?", (until, now, inviter["id"])
                        )
                        await db.execute(
                            "UPDATE users SET referred_by=? WHERE id=?",
                            (inviter["id"], user_id),
                        )
                        rewarded = True
            row = await (
                await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
            ).fetchone()
            await db.commit()
        return RegistrationResult(self._row_to_user(row), True, rewarded)

    async def upsert_user(
        self, telegram_id: int, username: str | None,
        first_name: str | None, last_name: str | None = None,
        full_name: str | None = None,
    ) -> User:
        return (
            await self.register_user(
                telegram_id, username, first_name,
                last_name=last_name, full_name=full_name,
            )
        ).user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            row = await (
                await db.execute(
                    "SELECT * FROM users WHERE telegram_id=?", (telegram_id,)
                )
            ).fetchone()
        return self._row_to_user(row) if row else None

    async def set_language(self, telegram_id: int, language: str) -> None:
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported language")
        async with self._connect() as db:
            await db.execute(
                "UPDATE users SET language=?, updated_at=? WHERE telegram_id=?",
                (language, self._now(), telegram_id),
            )
            await db.commit()

    async def activate_trial_once(
        self,
        telegram_id: int,
    ) -> TrialActivation | None:
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        expires = (
            now_dt + timedelta(hours=TRIAL_DURATION_HOURS)
        ).isoformat()
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")
            row = await (
                await db.execute(
                    "SELECT * FROM users WHERE telegram_id=?",
                    (telegram_id,),
                )
            ).fetchone()
            if row is None:
                await db.rollback()
                return None
            activated_now = not bool(row["trial_granted"])
            notification_required = (
                activated_now
                or not bool(row["trial_notification_sent"])
            )
            if activated_now:
                await db.execute(
                    "UPDATE users SET trial_granted=1, "
                    "trial_started_at=?, trial_expires_at=?, "
                    "trial_requests_used=0, trial_notification_sent=1, "
                    "updated_at=? WHERE id=?",
                    (now, expires, now, row["id"]),
                )
            elif notification_required:
                await db.execute(
                    "UPDATE users SET trial_notification_sent=1, "
                    "updated_at=? WHERE id=?",
                    (now, row["id"]),
                )
            row = await (
                await db.execute(
                    "SELECT * FROM users WHERE id=?", (row["id"],)
                )
            ).fetchone()
            await db.commit()
        return TrialActivation(
            self._row_to_user(row),
            activated_now,
            notification_required,
        )

    async def reserve_ai_request(
        self,
        user: User,
    ) -> AIRequestReservation:
        if user.is_blocked:
            return AIRequestReservation(False)
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")
            row = await (
                await db.execute(
                    "SELECT trial_granted, trial_expires_at, "
                    "trial_requests_used FROM users WHERE id=?",
                    (user.id,),
                )
            ).fetchone()
            if row:
                expires_at = row["trial_expires_at"]
                active = False
                if row["trial_granted"] and expires_at:
                    try:
                        expires = datetime.fromisoformat(expires_at)
                        if expires.tzinfo is None:
                            expires = expires.replace(tzinfo=timezone.utc)
                        active = (
                            expires > now_dt
                            and int(row["trial_requests_used"])
                            < TRIAL_AI_REQUEST_LIMIT
                        )
                    except ValueError:
                        active = False
                if active:
                    await db.execute(
                        "UPDATE users SET "
                        "trial_requests_used=trial_requests_used+1, "
                        "updated_at=? WHERE id=?",
                        (now, user.id),
                    )
                    await db.commit()
                    return AIRequestReservation(True, "trial")
            await db.rollback()
        allowed = await self.reserve_request(user)
        return AIRequestReservation(
            allowed,
            "plan" if allowed else None,
        )

    async def release_ai_request(
        self,
        user: User,
        reservation: AIRequestReservation,
    ) -> None:
        if not reservation.allowed:
            return
        if reservation.source == "trial":
            async with self._connect() as db:
                await db.execute(
                    "UPDATE users SET trial_requests_used="
                    "MAX(trial_requests_used-1, 0), updated_at=? "
                    "WHERE id=?",
                    (self._now(), user.id),
                )
                await db.commit()
        elif reservation.source == "plan":
            await self.release_request(user)

    async def update_user_preferences(
        self,
        telegram_id: int,
        *,
        category: str | None = None,
        target_ai: str | None = None,
        difficulty: str | None = None,
        response_style: str | None = None,
        workflow: str | None = None,
        export_format: str | None = None,
    ) -> None:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user is None:
            raise ValueError("User not found")
        values = {
            "last_category": category or user.last_category,
            "last_target_ai": target_ai or user.last_target_ai,
            "last_difficulty": difficulty or user.last_difficulty,
            "last_response_style": response_style or user.last_response_style,
            "last_workflow": workflow or user.last_workflow,
            "export_format": export_format or user.export_format,
        }
        validate_profile(
            values["last_category"],
            values["last_target_ai"],
            values["last_difficulty"],
            values["last_response_style"],
            values["last_workflow"],
        )
        if values["last_difficulty"] not in DIFFICULTIES:
            raise ValueError("Unsupported difficulty")
        if values["last_response_style"] not in RESPONSE_STYLES:
            raise ValueError("Unsupported response style")
        if values["last_workflow"] not in WORKFLOWS:
            raise ValueError("Unsupported workflow")
        if values["export_format"] not in EXPORT_FORMATS:
            raise ValueError("Unsupported export format")
        async with self._connect() as db:
            await db.execute(
                "UPDATE users SET last_category=?, last_target_ai=?, "
                "last_difficulty=?, last_response_style=?, last_workflow=?, "
                "export_format=?, updated_at=? WHERE telegram_id=?",
                (
                    values["last_category"],
                    values["last_target_ai"],
                    values["last_difficulty"],
                    values["last_response_style"],
                    values["last_workflow"],
                    values["export_format"],
                    self._now(),
                    telegram_id,
                ),
            )
            await db.commit()

    async def _reserve_daily(
        self, table: str, user: User, limit: int | None
    ) -> bool:
        if user.is_blocked:
            return False
        if limit is None:
            return True
        today, now = self._today(), self._now()
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")
            await db.execute(
                f"INSERT INTO {table} (user_id, usage_date, used_count, updated_at) "
                "VALUES (?, ?, 0, ?) ON CONFLICT(user_id, usage_date) DO NOTHING",
                (user.id, today, now),
            )
            row = await (
                await db.execute(
                    f"SELECT used_count FROM {table} "
                    "WHERE user_id=? AND usage_date=?", (user.id, today)
                )
            ).fetchone()
            if int(row["used_count"]) >= limit:
                await db.rollback()
                return False
            await db.execute(
                f"UPDATE {table} SET used_count=used_count+1, updated_at=? "
                "WHERE user_id=? AND usage_date=?", (now, user.id, today)
            )
            await db.commit()
        return True

    async def _release_daily(self, table: str, user: User) -> None:
        async with self._connect() as db:
            await db.execute(
                f"UPDATE {table} SET used_count=MAX(used_count-1, 0), "
                "updated_at=? WHERE user_id=? AND usage_date=?",
                (self._now(), user.id, self._today()),
            )
            await db.commit()

    async def reserve_request(self, user: User) -> bool:
        return await self._reserve_daily(
            "request_usage", user,
            get_plan_limits(user.plan).requests_daily_limit,
        )

    async def release_request(self, user: User) -> None:
        await self._release_daily("request_usage", user)

    async def reserve_improvement(self, user: User) -> bool:
        if user.trial_active:
            return True
        return await self._reserve_daily(
            "improvement_usage", user,
            get_plan_limits(user.plan).improvements_daily_limit,
        )

    async def release_improvement(self, user: User) -> None:
        await self._release_daily("improvement_usage", user)

    async def _usage(self, table: str, user: User, limit: int | None) -> Usage:
        async with self._connect() as db:
            row = await (
                await db.execute(
                    f"SELECT used_count FROM {table} "
                    "WHERE user_id=? AND usage_date=?",
                    (user.id, self._today()),
                )
            ).fetchone()
        return Usage(int(row[0]) if row else 0, limit)

    async def get_request_usage(self, user: User) -> Usage:
        return await self._usage(
            "request_usage", user,
            get_plan_limits(user.plan).requests_daily_limit,
        )

    async def get_improvement_usage(self, user: User) -> Usage:
        return await self._usage(
            "improvement_usage", user,
            get_plan_limits(
                user.entitlement_plan
            ).improvements_daily_limit,
        )

    async def save_prompt(
        self, user_id: int, category: str, target_ai: str,
        source_text: str, prompt_text: str, mode: str,
        language: str = "ru",
    ) -> int:
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported prompt language")
        async with self._connect() as db:
            cursor = await db.execute(
                "INSERT INTO prompts (user_id, category, target_ai, source_text, "
                "prompt_text, mode, language, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id, category, target_ai, source_text, prompt_text,
                    mode, language, self._now(),
                ),
            )
            await db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def _prompt(row: aiosqlite.Row) -> PromptRecord:
        return PromptRecord(
            row["id"], row["user_id"], row["category"], row["target_ai"],
            row["source_text"], row["prompt_text"], row["mode"], row["created_at"],
            row["language"],
        )

    async def get_prompt(self, prompt_id: int, user_id: int) -> PromptRecord | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            row = await (
                await db.execute(
                    "SELECT * FROM prompts WHERE id=? AND user_id=?",
                    (prompt_id, user_id),
                )
            ).fetchone()
        return self._prompt(row) if row else None

    async def get_prompt_history(self, user: User) -> list[PromptRecord]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    "SELECT * FROM prompts WHERE user_id=? "
                    "ORDER BY created_at DESC, id DESC LIMIT ?",
                    (
                        user.id,
                        get_plan_limits(
                            user.entitlement_plan
                        ).history_limit,
                    ),
                )
            ).fetchall()
        return [self._prompt(row) for row in rows]

    async def get_prompt_history_page(
        self,
        user: User,
        page: int,
        page_size: int = 5,
    ) -> PromptHistoryPage:
        history_limit = get_plan_limits(
            user.entitlement_plan
        ).history_limit
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            total_row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM prompts WHERE user_id=?",
                    (user.id,),
                )
            ).fetchone()
            total = min(int(total_row[0]), history_limit)
            total_pages = max(1, (total + page_size - 1) // page_size)
            current = min(max(page, 0), total_pages - 1)
            rows = await (
                await db.execute(
                    "SELECT * FROM prompts WHERE user_id=? "
                    "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                    (user.id, min(page_size, history_limit),
                     current * page_size),
                )
            ).fetchall()
        return PromptHistoryPage(
            [self._prompt(row) for row in rows],
            current,
            total,
            total_pages,
        )

    async def add_favorite(
        self,
        user_id: int,
        prompt_id: int,
        title: str,
    ) -> bool:
        async with self._connect() as db:
            cursor = await db.execute(
                """
                INSERT OR IGNORE INTO favorites (
                    user_id, prompt_id, title, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (user_id, prompt_id, title[:100], self._now()),
            )
            await db.commit()
        return cursor.rowcount == 1

    async def get_favorites(self, user_id: int) -> list[Favorite]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    """
                    SELECT
                        f.id AS favorite_id,
                        f.title AS favorite_title,
                        f.created_at AS favorite_created_at,
                        p.*
                    FROM favorites f
                    JOIN prompts p ON p.id = f.prompt_id
                    WHERE f.user_id = ?
                    ORDER BY f.created_at DESC, f.id DESC
                    """,
                    (user_id,),
                )
            ).fetchall()
        return [self._favorite(row) for row in rows]

    async def get_favorite(
        self,
        favorite_id: int,
        user_id: int,
    ) -> Favorite | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            row = await (
                await db.execute(
                    """
                    SELECT
                        f.id AS favorite_id,
                        f.title AS favorite_title,
                        f.created_at AS favorite_created_at,
                        p.*
                    FROM favorites f
                    JOIN prompts p ON p.id = f.prompt_id
                    WHERE f.id = ? AND f.user_id = ?
                    """,
                    (favorite_id, user_id),
                )
            ).fetchone()
        return self._favorite(row) if row else None

    def _favorite(self, row: aiosqlite.Row) -> Favorite:
        return Favorite(
            id=row["favorite_id"],
            user_id=row["user_id"],
            prompt_id=row["id"],
            title=row["favorite_title"],
            created_at=row["favorite_created_at"],
            prompt=self._prompt(row),
        )

    async def process_stars_payment(
        self, telegram_id: int, plan: str, currency: str, amount: int,
        payload: str, telegram_payment_charge_id: str,
        provider_payment_charge_id: str, duration_days: int = 30,
    ) -> bool:
        if plan not in {PRO, PREMIUM, PREMIUM_PLUS} or currency != "XTR":
            raise ValueError("Invalid paid plan or currency")
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")
            user = await (
                await db.execute(
                    "SELECT id, plan, plan_until FROM users WHERE telegram_id=?",
                    (telegram_id,),
                )
            ).fetchone()
            if not user:
                await db.rollback()
                return False
            inserted = await db.execute(
                "INSERT OR IGNORE INTO payments (user_id, plan, currency, amount, "
                "payload, telegram_payment_charge_id, provider_payment_charge_id, "
                "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user["id"], plan, currency, amount, payload,
                 telegram_payment_charge_id, provider_payment_charge_id, self._now()),
            )
            if inserted.rowcount != 1:
                await db.rollback()
                return False
            current = user["plan_until"] if user["plan"] == plan else None
            until = self._extend_until(current, duration_days)
            await db.execute(
                "UPDATE users SET plan=?, plan_until=?, premium_until=NULL, "
                "updated_at=? WHERE id=?",
                (plan, until, self._now(), user["id"]),
            )
            await db.commit()
        return True

    async def get_payment_by_charge_id(self, charge_id: str) -> Payment | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            row = await (
                await db.execute(
                    "SELECT * FROM payments WHERE telegram_payment_charge_id=?",
                    (charge_id,),
                )
            ).fetchone()
        return Payment(**dict(row)) if row else None

    async def get_referral_count(self, user_id: int) -> int:
        async with self._connect() as db:
            row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM referrals WHERE inviter_id=?", (user_id,)
                )
            ).fetchone()
        return int(row[0])

    async def set_admin_user_plan(self, user_id: int, plan: str) -> bool:
        if plan not in VALID_PLANS:
            raise ValueError("Unsupported plan")
        async with self._connect() as db:
            cursor = await db.execute(
                "UPDATE users SET plan=?, plan_until=NULL, premium_until=NULL, "
                "updated_at=? WHERE id=?", (plan, self._now(), user_id)
            )
            await db.commit()
        return cursor.rowcount == 1

    async def extend_admin_user_premium(self, user_id: int, days: int = 3) -> bool:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute("BEGIN IMMEDIATE")
            row = await (
                await db.execute(
                    "SELECT premium_until FROM users WHERE id=?", (user_id,)
                )
            ).fetchone()
            if not row:
                await db.rollback()
                return False
            until = self._extend_until(row["premium_until"], days)
            await db.execute(
                "UPDATE users SET premium_until=?, updated_at=? WHERE id=?",
                (until, self._now(), user_id),
            )
            await db.commit()
        return True

    async def set_user_blocked(self, user_id: int, blocked: bool) -> bool:
        async with self._connect() as db:
            cursor = await db.execute(
                "UPDATE users SET is_blocked=?, updated_at=? WHERE id=?",
                (int(blocked), self._now(), user_id),
            )
            await db.commit()
        return cursor.rowcount == 1

    async def set_user_blocked_by_telegram_id(
        self,
        telegram_id: int,
        blocked: bool,
    ) -> bool:
        async with self._connect() as db:
            cursor = await db.execute(
                "UPDATE users SET is_blocked=?, updated_at=? "
                "WHERE telegram_id=?",
                (int(blocked), self._now(), telegram_id),
            )
            await db.commit()
        return cursor.rowcount == 1

    async def get_broadcast_recipients(
        self,
        audience: str,
    ) -> list[BroadcastRecipient]:
        if audience not in {"all", "free", "paid", "premium"}:
            raise ValueError("Unsupported broadcast audience")
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    "SELECT * FROM users WHERE is_blocked=0 "
                    "ORDER BY id"
                )
            ).fetchall()
        recipients = []
        for row in rows:
            user = self._row_to_user(row)
            include = (
                audience == "all"
                or (audience == "free" and user.plan == FREE)
                or (
                    audience == "paid"
                    and user.plan in {PRO, PREMIUM, PREMIUM_PLUS}
                )
                or (
                    audience == "premium"
                    and user.plan in {PREMIUM, PREMIUM_PLUS}
                )
            )
            if include:
                recipients.append(
                    BroadcastRecipient(
                        user.id,
                        user.telegram_id,
                        user.plan,
                        user.language or "ru",
                    )
                )
        return recipients

    async def save_news(
        self,
        title: str,
        text: str,
        language: str,
    ) -> int:
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported news language")
        async with self._connect() as db:
            cursor = await db.execute(
                "INSERT INTO news (title, text, language, created_at) "
                "VALUES (?, ?, ?, ?)",
                (title[:200], text, language, self._now()),
            )
            await db.commit()
        return int(cursor.lastrowid)

    async def get_news(
        self,
        language: str,
        limit: int = 20,
    ) -> list[NewsItem]:
        if language not in {"ru", "en"}:
            language = "ru"
        safe_limit = max(1, min(limit, 20))
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    "SELECT * FROM news WHERE language=? "
                    "ORDER BY created_at DESC, id DESC LIMIT ?",
                    (language, safe_limit),
                )
            ).fetchall()
        return [NewsItem(**dict(row)) for row in rows]

    @staticmethod
    def _validate_assistant(assistant: str) -> None:
        if assistant not in {"gpt", "claude", "gemini"}:
            raise ValueError("Unsupported assistant")

    async def create_assistant_chat(
        self,
        user_id: int,
        assistant: str,
        title: str,
    ) -> AssistantChat:
        self._validate_assistant(assistant)
        now = self._now()
        clean_title = title.strip()[:120] or "New chat"
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "INSERT INTO assistant_chats "
                "(user_id, assistant, title, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, assistant, clean_title, now, now),
            )
            row = await (
                await db.execute(
                    "SELECT * FROM assistant_chats WHERE id=?",
                    (cursor.lastrowid,),
                )
            ).fetchone()
            await db.commit()
        return AssistantChat(**dict(row))

    async def get_assistant_chats(
        self,
        user_id: int,
        assistant: str,
        search: str | None = None,
        limit: int = 50,
    ) -> list[AssistantChat]:
        self._validate_assistant(assistant)
        where = "c.user_id=? AND c.assistant=?"
        params: list[object] = [user_id, assistant]
        if search:
            where += (
                " AND (LOWER(c.title) LIKE LOWER(?) OR EXISTS ("
                "SELECT 1 FROM assistant_messages m "
                "WHERE m.chat_id=c.id AND LOWER(m.content) LIKE LOWER(?)))"
            )
            token = f"%{search.strip()}%"
            params.extend([token, token])
        params.append(max(1, min(limit, 100)))
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    f"SELECT c.* FROM assistant_chats c WHERE {where} "
                    "ORDER BY c.updated_at DESC, c.id DESC LIMIT ?",
                    params,
                )
            ).fetchall()
        return [AssistantChat(**dict(row)) for row in rows]

    async def get_assistant_chat(
        self,
        chat_id: int,
        user_id: int,
        assistant: str,
    ) -> AssistantChat | None:
        self._validate_assistant(assistant)
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            row = await (
                await db.execute(
                    "SELECT * FROM assistant_chats "
                    "WHERE id=? AND user_id=? AND assistant=?",
                    (chat_id, user_id, assistant),
                )
            ).fetchone()
        return AssistantChat(**dict(row)) if row else None

    async def add_assistant_message(
        self,
        chat_id: int,
        user_id: int,
        assistant: str,
        role: str,
        content: str,
    ) -> AssistantMessage:
        self._validate_assistant(assistant)
        if role not in {"user", "assistant"}:
            raise ValueError("Unsupported assistant message role")
        chat = await self.get_assistant_chat(chat_id, user_id, assistant)
        if chat is None:
            raise ValueError("Assistant chat not found")
        now = self._now()
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "INSERT INTO assistant_messages "
                "(chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, now),
            )
            await db.execute(
                "UPDATE assistant_chats SET updated_at=? WHERE id=?",
                (now, chat_id),
            )
            row = await (
                await db.execute(
                    "SELECT * FROM assistant_messages WHERE id=?",
                    (cursor.lastrowid,),
                )
            ).fetchone()
            await db.commit()
        return AssistantMessage(**dict(row))

    async def get_assistant_messages(
        self,
        chat_id: int,
        user_id: int,
        assistant: str,
        limit: int = 100,
    ) -> list[AssistantMessage]:
        self._validate_assistant(assistant)
        chat = await self.get_assistant_chat(chat_id, user_id, assistant)
        if chat is None:
            return []
        safe_limit = max(1, min(limit, 200))
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            rows = await (
                await db.execute(
                    "SELECT * FROM ("
                    "SELECT * FROM assistant_messages WHERE chat_id=? "
                    "ORDER BY id DESC LIMIT ?) ORDER BY id",
                    (chat_id, safe_limit),
                )
            ).fetchall()
        return [AssistantMessage(**dict(row)) for row in rows]

    async def rename_assistant_chat(
        self,
        chat_id: int,
        user_id: int,
        assistant: str,
        title: str,
    ) -> bool:
        self._validate_assistant(assistant)
        async with self._connect() as db:
            cursor = await db.execute(
                "UPDATE assistant_chats SET title=?, updated_at=? "
                "WHERE id=? AND user_id=? AND assistant=?",
                (
                    title.strip()[:120] or "New chat",
                    self._now(),
                    chat_id,
                    user_id,
                    assistant,
                ),
            )
            await db.commit()
        return cursor.rowcount == 1

    async def delete_assistant_chat(
        self,
        chat_id: int,
        user_id: int,
        assistant: str,
    ) -> bool:
        self._validate_assistant(assistant)
        async with self._connect() as db:
            cursor = await db.execute(
                "DELETE FROM assistant_chats "
                "WHERE id=? AND user_id=? AND assistant=?",
                (chat_id, user_id, assistant),
            )
            await db.commit()
        return cursor.rowcount == 1

    def _admin_basic(self, row: aiosqlite.Row) -> AdminUser:
        user = self._row_to_user(row)
        return AdminUser(
            row["id"], row["telegram_id"], row["username"], row["first_name"],
            row["last_name"], row["full_name"], row["language"], user.plan,
            row["plan_until"], row["premium_until"], bool(row["is_blocked"]),
            row["created_at"],
        )

    async def get_admin_statistics(self) -> AdminStatistics:
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            users = await (await db.execute("SELECT * FROM users")).fetchall()
            new_users = (await (await db.execute(
                "SELECT COUNT(*) FROM users WHERE created_at>=?", (since,)
            )).fetchone())[0]
            pay = await (await db.execute(
                "SELECT COALESCE(SUM(amount),0) revenue, "
                "SUM(CASE WHEN plan='pro' THEN 1 ELSE 0 END) pro_sales, "
                "SUM(CASE WHEN plan='premium' THEN 1 ELSE 0 END) premium_sales, "
                "SUM(CASE WHEN plan='premium_plus' THEN 1 ELSE 0 END) "
                "premium_plus_sales "
                "FROM payments WHERE currency='XTR'"
            )).fetchone()
            total = (await (await db.execute(
                "SELECT COUNT(*) FROM prompts"
            )).fetchone())[0]
            today = (await (await db.execute(
                "SELECT COALESCE(SUM(used_count),0) FROM request_usage "
                "WHERE usage_date=?", (self._today(),)
            )).fetchone())[0]
        counts = {FREE: 0, PRO: 0, PREMIUM: 0, PREMIUM_PLUS: 0}
        for row in users:
            counts[self._row_to_user(row).plan] += 1
        return AdminStatistics(
            len(users), counts[FREE], counts[PRO], counts[PREMIUM],
            int(new_users), int(pay["revenue"] or 0),
            int(pay["pro_sales"] or 0), int(pay["premium_sales"] or 0),
            int(total), int(today), counts[PREMIUM_PLUS],
            int(pay["premium_plus_sales"] or 0),
        )

    async def get_admin_users_page(
        self, page: int, page_size: int = 10, search: str | None = None,
    ) -> AdminUserPage:
        where, params = "", []
        if search:
            clean = search.strip().lstrip("@")
            if clean.isdigit():
                where, params = "WHERE telegram_id=?", [int(clean)]
            else:
                where, params = "WHERE LOWER(username) LIKE LOWER(?)", [f"%{clean}%"]
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            count = (await (await db.execute(
                f"SELECT COUNT(*) FROM users {where}", params
            )).fetchone())[0]
            pages = max(1, (int(count) + page_size - 1) // page_size)
            current = min(max(page, 0), pages - 1)
            rows = await (await db.execute(
                f"SELECT * FROM users {where} ORDER BY created_at DESC, id DESC "
                "LIMIT ? OFFSET ?", [*params, page_size, current * page_size]
            )).fetchall()
        return AdminUserPage(
            [self._admin_basic(row) for row in rows],
            current, int(count), pages,
        )

    async def get_admin_user(self, user_id: int) -> AdminUser | None:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute(
                "SELECT u.*, COALESCE(r.used_count,0) requests_today, "
                "(SELECT COUNT(*) FROM prompts p WHERE p.user_id=u.id) prompts_total, "
                "(SELECT COUNT(*) FROM referrals f WHERE f.inviter_id=u.id) referrals_count "
                "FROM users u LEFT JOIN request_usage r ON r.user_id=u.id "
                "AND r.usage_date=? WHERE u.id=?", (self._today(), user_id)
            )).fetchone()
        if not row:
            return None
        basic = self._admin_basic(row)
        return AdminUser(
            basic.user_id, basic.telegram_id, basic.username, basic.first_name,
            basic.last_name, basic.full_name, basic.language, basic.plan,
            basic.plan_until, basic.premium_until, basic.is_blocked,
            basic.created_at, int(row["requests_today"]),
            int(row["prompts_total"]), int(row["referrals_count"]),
        )

    async def get_admin_referral_report(self) -> AdminReferralReport:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            total = (await (await db.execute(
                "SELECT COUNT(*) FROM referrals"
            )).fetchone())[0]
            top = await (await db.execute(
                "SELECT u.*, COUNT(*) invited_count FROM referrals r "
                "JOIN users u ON u.id=r.inviter_id GROUP BY u.id "
                "ORDER BY invited_count DESC LIMIT 10"
            )).fetchall()
            rows = await (await db.execute(
                "SELECT i.full_name inviter_name, i.username inviter_username, "
                "n.full_name invited_name, n.username invited_username, r.created_at "
                "FROM referrals r JOIN users i ON i.id=r.inviter_id "
                "JOIN users n ON n.id=r.invited_id ORDER BY r.created_at DESC"
            )).fetchall()
        return AdminReferralReport(
            int(total),
            [AdminReferrer(
                row["full_name"] or row["first_name"] or "—",
                row["username"], int(row["invited_count"])
            ) for row in top],
            [AdminReferral(
                row["inviter_name"] or "—", row["inviter_username"],
                row["invited_name"] or "—", row["invited_username"],
                row["created_at"]
            ) for row in rows],
        )
