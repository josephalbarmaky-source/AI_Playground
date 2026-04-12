"""Tool dispatcher — executes a parsed tool call against the user's DB + services."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .db import UserDB
from .tools.search import format_results, web_search
from .tools.timeparse import parse_when


class ToolError(Exception):
    pass


async def dispatch(
    tool_name: str,
    args: dict[str, Any],
    db: UserDB,
    timezone: str,
    schedule_reminder_cb,
) -> str:
    """Execute a tool and return a user-facing string.

    `schedule_reminder_cb` is a callable (reminder_id, fire_at_utc, text) -> None
    that arms the APScheduler job so it fires via Telegram at the right time.
    """
    try:
        if tool_name == "add_reminder":
            text = str(args.get("text", "")).strip()
            when = str(args.get("when", "")).strip()
            if not text or not when:
                raise ToolError("I need both the reminder text and when to fire it.")
            fire_at = parse_when(when, tz=timezone)
            if fire_at is None:
                raise ToolError(
                    f"I couldn't understand the time '{when}'. Try 'in 10 minutes' or 'tomorrow at 3pm'."
                )
            rid = await db.add_reminder(text, fire_at.isoformat())
            schedule_reminder_cb(rid, fire_at, text)
            local = fire_at.astimezone(ZoneInfo(timezone))
            return f"✅ Reminder set for {local.strftime('%a %d %b, %H:%M')} — \"{text}\""

        if tool_name == "list_reminders":
            rems = await db.list_reminders()
            if not rems:
                return "You have no upcoming reminders."
            lines = ["📅 Upcoming reminders:"]
            for r in rems:
                ts = datetime.fromisoformat(r["fire_at"]).astimezone(ZoneInfo(timezone))
                lines.append(f"  • {ts.strftime('%a %d %b, %H:%M')} — {r['text']}")
            return "\n".join(lines)

        if tool_name == "add_task":
            title = str(args.get("title", "")).strip()
            notes = args.get("notes")
            if not title:
                raise ToolError("What's the task?")
            tid = await db.add_task(title, notes)
            return f"✅ Added task #{tid}: {title}"

        if tool_name == "list_tasks":
            tasks = await db.list_tasks()
            if not tasks:
                return "Your to-do list is empty."
            lines = ["📝 Your to-do list:"]
            for t in tasks:
                lines.append(f"  • #{t['id']} — {t['title']}")
            return "\n".join(lines)

        if tool_name == "complete_task":
            tid = int(args.get("id", 0))
            if not tid:
                raise ToolError("Which task ID should I complete?")
            ok = await db.complete_task(tid)
            return f"✅ Marked task #{tid} done." if ok else f"I couldn't find task #{tid}."

        if tool_name == "delete_task":
            tid = int(args.get("id", 0))
            if not tid:
                raise ToolError("Which task ID should I delete?")
            ok = await db.delete_task(tid)
            return f"🗑 Deleted task #{tid}." if ok else f"I couldn't find task #{tid}."

        if tool_name == "web_search":
            query = str(args.get("query", "")).strip()
            if not query:
                raise ToolError("What should I search for?")
            results = await web_search(query)
            return f"🔎 Results for \"{query}\":\n\n{format_results(results)}"

        raise ToolError(f"Unknown tool: {tool_name}")

    except ToolError as e:
        return f"⚠️ {e}"
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Tool error: {e}"
