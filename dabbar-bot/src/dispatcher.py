"""Tool dispatcher — executes a parsed tool call against the user's DB + services."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .db import UserDB
from .tools.calendar import create_event, list_events, update_event
from .tools.expenses import add_expense as add_expense_fn
from .tools.expenses import expense_summary as expense_summary_fn
from .tools.expenses import list_expenses as list_expenses_fn
from .tools.gmail import draft_email, list_emails, read_email, send_email
from .tools.google_auth import get_auth_url
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

        if tool_name == "connect_google":
            url = get_auth_url(db.user_id)
            return f"🔗 To connect your Google account, open this link:\n{url}\n\nAfter authorizing, you'll get a confirmation here."

        if tool_name == "list_events":
            days = int(args.get("days", 1))
            events = await list_events(db, timezone, days=days)
            if not events:
                return "Your calendar is clear!" if days == 1 else f"No events in the next {days} days."
            lines = [f"📅 Events for the next {'day' if days == 1 else f'{days} days'}:"]
            for ev in events:
                start = ev["start"]
                try:
                    t = datetime.fromisoformat(start).astimezone(ZoneInfo(timezone))
                    time_str = t.strftime("%a %d %b, %H:%M")
                except Exception:
                    time_str = start
                loc = f" @ {ev['location']}" if ev.get("location") else ""
                lines.append(f"  • {time_str} — {ev['summary']}{loc}")
            return "\n".join(lines)

        if tool_name == "create_event":
            summary = str(args.get("summary", "")).strip()
            start = str(args.get("start", "")).strip()
            end = str(args.get("end", "")).strip()
            if not summary or not start or not end:
                raise ToolError("I need at least a summary, start time, and end time.")
            result = await create_event(
                db, timezone, summary, start, end,
                description=args.get("description", ""),
                location=args.get("location", ""),
            )
            return f"✅ Event created: {result['summary']}\n🔗 {result.get('htmlLink', '')}"

        if tool_name == "update_event":
            event_id = str(args.get("event_id", "")).strip()
            if not event_id:
                raise ToolError("Which event should I update? I need the event_id.")
            result = await update_event(
                db, timezone, event_id,
                summary=args.get("summary"),
                start=args.get("start"),
                end=args.get("end"),
                description=args.get("description"),
                location=args.get("location"),
            )
            return f"✅ Event updated: {result['summary']}"

        if tool_name == "list_emails":
            max_results = int(args.get("max_results", 5))
            query = str(args.get("query", "is:inbox is:unread")).strip()
            emails = await list_emails(db, max_results=max_results, query=query)
            if not emails:
                return "📭 No emails found."
            lines = [f"📧 {len(emails)} emails:"]
            for e in emails:
                lines.append(f"  • [{e['id'][:8]}] From: {e['from']}\n    Subject: {e['subject']}\n    {e['snippet'][:80]}...")
            return "\n".join(lines)

        if tool_name == "read_email":
            email_id = str(args.get("email_id", "")).strip()
            if not email_id:
                raise ToolError("Which email? I need the email_id.")
            email = await read_email(db, email_id)
            return f"📧 *{email['subject']}*\nFrom: {email['from']}\nDate: {email['date']}\n\n{email['body'][:1500]}"

        if tool_name == "draft_email":
            to = str(args.get("to", "")).strip()
            subject = str(args.get("subject", "")).strip()
            body = str(args.get("body", "")).strip()
            if not to or not subject:
                raise ToolError("I need at least a recipient (to) and subject.")
            result = await draft_email(db, to, subject, body)
            return f"✅ Draft created: {subject}\nDraft ID: {result['id']}"

        if tool_name == "send_email":
            to = str(args.get("to", "")).strip()
            subject = str(args.get("subject", "")).strip()
            body = str(args.get("body", "")).strip()
            if not to or not subject:
                raise ToolError("I need at least a recipient (to) and subject.")
            result = await send_email(db, to, subject, body)
            return f"✅ {result['message']}"

        if tool_name == "add_expense":
            amount = float(args.get("amount", 0))
            if amount <= 0:
                raise ToolError("What's the amount?")
            category = str(args.get("category", "other")).strip()
            description = str(args.get("description", "")).strip()
            currency = str(args.get("currency", "AED")).strip()
            result = await add_expense_fn(db, amount, category, description, currency)
            return f"💰 Expense recorded: {result['currency']} {result['amount']:.2f} ({result['category']})"

        if tool_name == "list_expenses":
            limit = int(args.get("limit", 10))
            category = args.get("category")
            expenses = await list_expenses_fn(db, limit=limit, category=category)
            if not expenses:
                return "No expenses recorded yet."
            lines = ["💳 Recent expenses:"]
            for e in expenses:
                lines.append(f"  • #{e['id']} {e['currency']} {e['amount']:.2f} — {e['category']}: {e['description'] or '(no note)'} ({e['created_at'][:10]})")
            return "\n".join(lines)

        if tool_name == "expense_summary":
            days = int(args.get("days", 30))
            summary = await expense_summary_fn(db, days=days)
            if not summary:
                return f"No expenses in the last {days} days."
            total = sum(s["total"] for s in summary)
            lines = [f"📊 Spending summary (last {days} days): AED {total:.2f} total\n"]
            for s in summary:
                pct = (s["total"] / total * 100) if total else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                lines.append(f"  {s['category']:15s} AED {s['total']:>8.2f} ({s['count']} items) {bar}")
            return "\n".join(lines)

        raise ToolError(f"Unknown tool: {tool_name}")

    except ToolError as e:
        return f"⚠️ {e}"
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Tool error: {e}"
