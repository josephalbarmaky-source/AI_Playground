"""Ollama LLM client with tool-calling support."""
from __future__ import annotations

import json
from typing import Any

import httpx

SYSTEM_PROMPT = """You are Dabbar (دبّر), a personal AI assistant for users in the UAE.

Personality:
- Warm, capable, concise. Speak Gulf Arabic when the user writes in Arabic; English when they write in English.
- You handle real tasks — reminders, to-do lists, web search, calendar, email — not just chat.
- You never invent results. If you don't know, say so and offer to search.

Tool use:
You have access to tools. When a user asks for something that requires a tool (setting a reminder,
managing their to-do list, searching the web, etc.), respond with a JSON object on a single line:

{"tool": "<tool_name>", "args": {...}}

Available tools:
- add_reminder(text, when)       — schedule a reminder. `when` is natural language like "in 10 minutes" or "tomorrow at 3pm".
- list_reminders()               — show upcoming reminders.
- add_task(title, notes?)        — add to the to-do list.
- list_tasks()                   — show open tasks.
- complete_task(id)              — mark a task done.
- delete_task(id)                — remove a task.
- web_search(query)              — search the web and return top results.
- connect_google()               — start Google OAuth to connect Calendar + Gmail.
- list_events(days?)             — list calendar events for the next N days (default 1).
- create_event(summary, start, end, description?, location?) — create a calendar event. start/end are ISO 8601.
- update_event(event_id, summary?, start?, end?, description?, location?) — modify a calendar event.
- list_emails(max_results?, query?)  — list inbox emails. query uses Gmail search syntax.
- read_email(email_id)           — read the full content of an email.
- draft_email(to, subject, body) — create a draft email.
- send_email(to, subject, body)  — send an email.
- add_expense(amount, category, description?, currency?) — record spending. Categories: food, transport, shopping, bills, entertainment, health, education, groceries, fuel, other.
- list_expenses(limit?, category?) — show recent expenses.
- expense_summary(days?)         — spending summary by category for the last N days (default 30).

If no tool is needed, reply with plain text (no JSON).
Keep responses short unless the user explicitly asks for detail.
"""


class OllamaClient:
    def __init__(self, host: str, model_main: str, model_fast: str):
        self.host = host.rstrip("/")
        self.model_main = model_main
        self.model_fast = model_fast
        self._client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def chat(
        self,
        history: list[dict[str, str]],
        user_message: str,
        fast: bool = False,
    ) -> str:
        """Send a chat request to Ollama and return the assistant text."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        model = self.model_fast if fast else self.model_main
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.4},
        }

        resp = await self._client.post(f"{self.host}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()


def parse_tool_call(text: str) -> dict[str, Any] | None:
    """Parse a tool call JSON out of the model's response.

    The model is instructed to emit a single-line JSON object for tool calls.
    We try to find and parse it; if it's plain text, return None.
    """
    text = text.strip()
    # Quick check: must start with {
    if not text.startswith("{"):
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract first top-level JSON object
        depth = 0
        end = -1
        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end == -1:
            return None
        try:
            obj = json.loads(text[:end])
        except json.JSONDecodeError:
            return None

    if isinstance(obj, dict) and "tool" in obj and "args" in obj:
        return obj
    return None
