"""Per-user SQLite storage for Dabbar.

Each Telegram user gets an isolated SQLite file so tenants never share tables.
Files live under DABBAR_DATA_DIR as `user_<telegram_id>.db`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    notes TEXT,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    fire_at TEXT NOT NULL,      -- ISO 8601 UTC
    fired INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,          -- 'user' | 'assistant' | 'tool'
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS profile (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS google_tokens (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_uri TEXT NOT NULL DEFAULT 'https://oauth2.googleapis.com/token',
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    scopes TEXT NOT NULL,
    expiry TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_payment_charge_id TEXT NOT NULL,
    provider_payment_charge_id TEXT,
    amount INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'XTR',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'AED',
    category TEXT NOT NULL DEFAULT 'other',
    description TEXT,
    receipt_file_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class UserDB:
    """Async per-user SQLite wrapper."""

    def __init__(self, data_dir: Path, user_id: int):
        self.path = data_dir / f"user_{user_id}.db"
        self.user_id = user_id

    async def _connect(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.path)
        await conn.executescript(SCHEMA)
        await conn.commit()
        return conn

    # ---- Tasks ----
    async def add_task(self, title: str, notes: str | None = None) -> int:
        async with await self._connect() as conn:
            cur = await conn.execute(
                "INSERT INTO tasks (title, notes) VALUES (?, ?)", (title, notes)
            )
            await conn.commit()
            return cur.lastrowid or 0

    async def list_tasks(self, include_done: bool = False) -> list[dict[str, Any]]:
        query = "SELECT id, title, notes, done, created_at FROM tasks"
        if not include_done:
            query += " WHERE done = 0"
        query += " ORDER BY id DESC"
        async with await self._connect() as conn:
            async with conn.execute(query) as cur:
                rows = await cur.fetchall()
        return [
            {"id": r[0], "title": r[1], "notes": r[2], "done": bool(r[3]), "created_at": r[4]}
            for r in rows
        ]

    async def complete_task(self, task_id: int) -> bool:
        async with await self._connect() as conn:
            cur = await conn.execute(
                "UPDATE tasks SET done = 1, completed_at = datetime('now') WHERE id = ?",
                (task_id,),
            )
            await conn.commit()
            return cur.rowcount > 0

    async def delete_task(self, task_id: int) -> bool:
        async with await self._connect() as conn:
            cur = await conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await conn.commit()
            return cur.rowcount > 0

    # ---- Reminders ----
    async def add_reminder(self, text: str, fire_at_iso: str) -> int:
        async with await self._connect() as conn:
            cur = await conn.execute(
                "INSERT INTO reminders (text, fire_at) VALUES (?, ?)", (text, fire_at_iso)
            )
            await conn.commit()
            return cur.lastrowid or 0

    async def list_reminders(self, include_fired: bool = False) -> list[dict[str, Any]]:
        query = "SELECT id, text, fire_at, fired FROM reminders"
        if not include_fired:
            query += " WHERE fired = 0"
        query += " ORDER BY fire_at ASC"
        async with await self._connect() as conn:
            async with conn.execute(query) as cur:
                rows = await cur.fetchall()
        return [{"id": r[0], "text": r[1], "fire_at": r[2], "fired": bool(r[3])} for r in rows]

    async def mark_reminder_fired(self, reminder_id: int) -> None:
        async with await self._connect() as conn:
            await conn.execute(
                "UPDATE reminders SET fired = 1 WHERE id = ?", (reminder_id,)
            )
            await conn.commit()

    # ---- Conversation history ----
    async def add_message(self, role: str, content: str) -> None:
        async with await self._connect() as conn:
            await conn.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)", (role, content)
            )
            await conn.commit()

    async def recent_messages(self, limit: int = 12) -> list[dict[str, str]]:
        async with await self._connect() as conn:
            async with conn.execute(
                "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
            ) as cur:
                rows = await cur.fetchall()
        # reverse to chronological
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    async def clear_messages(self) -> None:
        async with await self._connect() as conn:
            await conn.execute("DELETE FROM messages")
            await conn.commit()

    # ---- Profile ----
    async def get_profile(self, key: str) -> str | None:
        async with await self._connect() as conn:
            async with conn.execute(
                "SELECT value FROM profile WHERE key = ?", (key,)
            ) as cur:
                row = await cur.fetchone()
        return row[0] if row else None

    async def set_profile(self, key: str, value: str) -> None:
        async with await self._connect() as conn:
            await conn.execute(
                "INSERT OR REPLACE INTO profile (key, value) VALUES (?, ?)",
                (key, value),
            )
            await conn.commit()

    # ---- Google tokens ----
    async def save_google_tokens(self, token_data: dict[str, Any]) -> None:
        async with await self._connect() as conn:
            await conn.execute(
                """INSERT OR REPLACE INTO google_tokens
                   (id, access_token, refresh_token, token_uri, client_id, client_secret, scopes, expiry)
                   VALUES (1, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    token_data["access_token"],
                    token_data.get("refresh_token"),
                    token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                    token_data["client_id"],
                    token_data["client_secret"],
                    json.dumps(token_data.get("scopes", [])),
                    token_data.get("expiry"),
                ),
            )
            await conn.commit()

    async def get_google_tokens(self) -> dict[str, Any] | None:
        async with await self._connect() as conn:
            async with conn.execute(
                "SELECT access_token, refresh_token, token_uri, client_id, client_secret, scopes, expiry "
                "FROM google_tokens WHERE id = 1"
            ) as cur:
                row = await cur.fetchone()
        if not row:
            return None
        return {
            "access_token": row[0],
            "refresh_token": row[1],
            "token_uri": row[2],
            "client_id": row[3],
            "client_secret": row[4],
            "scopes": json.loads(row[5]),
            "expiry": row[6],
        }

    async def delete_google_tokens(self) -> None:
        async with await self._connect() as conn:
            await conn.execute("DELETE FROM google_tokens")
            await conn.commit()

    # ---- Subscriptions ----
    async def add_subscription(
        self,
        telegram_charge_id: str,
        provider_charge_id: str | None,
        amount: int,
        expires_at: str,
    ) -> int:
        async with await self._connect() as conn:
            cur = await conn.execute(
                """INSERT INTO subscriptions
                   (telegram_payment_charge_id, provider_payment_charge_id, amount, expires_at)
                   VALUES (?, ?, ?, ?)""",
                (telegram_charge_id, provider_charge_id, amount, expires_at),
            )
            await conn.commit()
            return cur.lastrowid or 0

    async def is_subscribed(self) -> bool:
        async with await self._connect() as conn:
            async with conn.execute(
                "SELECT 1 FROM subscriptions WHERE status = 'active' AND expires_at > datetime('now') LIMIT 1"
            ) as cur:
                row = await cur.fetchone()
        return row is not None

    async def get_subscription_info(self) -> dict[str, Any] | None:
        async with await self._connect() as conn:
            async with conn.execute(
                """SELECT id, amount, currency, status, created_at, expires_at
                   FROM subscriptions WHERE status = 'active'
                   ORDER BY expires_at DESC LIMIT 1"""
            ) as cur:
                row = await cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0], "amount": row[1], "currency": row[2],
            "status": row[3], "created_at": row[4], "expires_at": row[5],
        }

    # ---- Expenses ----
    async def add_expense(
        self,
        amount: float,
        category: str,
        description: str = "",
        currency: str = "AED",
        receipt_file_id: str | None = None,
    ) -> int:
        async with await self._connect() as conn:
            cur = await conn.execute(
                "INSERT INTO expenses (amount, currency, category, description, receipt_file_id) VALUES (?, ?, ?, ?, ?)",
                (amount, currency, category, description, receipt_file_id),
            )
            await conn.commit()
            return cur.lastrowid or 0

    async def list_expenses(self, limit: int = 20, category: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT id, amount, currency, category, description, created_at FROM expenses"
        params: list[Any] = []
        if category:
            query += " WHERE category = ?"
            params.append(category)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        async with await self._connect() as conn:
            async with conn.execute(query, params) as cur:
                rows = await cur.fetchall()
        return [
            {"id": r[0], "amount": r[1], "currency": r[2], "category": r[3],
             "description": r[4], "created_at": r[5]}
            for r in rows
        ]

    async def expense_summary(self, days: int = 30) -> list[dict[str, Any]]:
        async with await self._connect() as conn:
            async with conn.execute(
                """SELECT category, SUM(amount) as total, COUNT(*) as count
                   FROM expenses
                   WHERE created_at > datetime('now', ?)
                   GROUP BY category ORDER BY total DESC""",
                (f"-{days} days",),
            ) as cur:
                rows = await cur.fetchall()
        return [{"category": r[0], "total": r[1], "count": r[2]} for r in rows]
