"""Per-user SQLite storage for Dabbar.

Each Telegram user gets an isolated SQLite file so tenants never share tables.
Files live under DABBAR_DATA_DIR as `user_<telegram_id>.db`.
"""
from __future__ import annotations

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
