"""Lightweight natural language time parser.

Handles the common cases we need for reminders without pulling in heavy deps.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_REL_RE = re.compile(
    r"in\s+(\d+)\s+(second|seconds|minute|minutes|min|mins|hour|hours|hr|hrs|day|days)",
    re.IGNORECASE,
)
_AT_RE = re.compile(
    r"(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
    re.IGNORECASE,
)


def parse_when(text: str, tz: str = "Asia/Dubai") -> datetime | None:
    """Parse natural language time into a timezone-aware UTC datetime.

    Supported patterns:
      - "in 10 minutes", "in 2 hours", "in 3 days"
      - "tomorrow at 3pm", "tomorrow 9am", "today at 5:30pm"
      - "at 15:30", "3pm"
    Returns None if parsing fails.
    """
    tzinfo = ZoneInfo(tz)
    now = datetime.now(tzinfo)
    text = text.strip().lower()

    # Relative: "in N units"
    m = _REL_RE.search(text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("sec"):
            delta = timedelta(seconds=n)
        elif unit.startswith("min"):
            delta = timedelta(minutes=n)
        elif unit.startswith("hour") or unit.startswith("hr"):
            delta = timedelta(hours=n)
        elif unit.startswith("day"):
            delta = timedelta(days=n)
        else:
            return None
        return (now + delta).astimezone(ZoneInfo("UTC"))

    # Absolute: "tomorrow"/"today" + optional time
    day_offset = 0
    if "tomorrow" in text:
        day_offset = 1
    elif "today" in text:
        day_offset = 0
    elif "tonight" in text:
        day_offset = 0

    m = _AT_RE.search(text)
    if not m:
        return None

    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = m.group(3)
    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    # "tonight" with no am/pm — assume evening
    if "tonight" in text and not ampm and hour < 12:
        hour += 12

    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    target += timedelta(days=day_offset)

    # If no day offset and time already passed today, bump to tomorrow
    if day_offset == 0 and target < now:
        target += timedelta(days=1)

    return target.astimezone(ZoneInfo("UTC"))
