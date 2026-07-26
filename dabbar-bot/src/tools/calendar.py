"""Google Calendar tool functions."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build

from ..db import UserDB
from .google_auth import get_credentials


async def _get_service(db: UserDB):
    creds = await get_credentials(db)
    if not creds:
        raise RuntimeError("Google account not connected. Send /connect to link your account.")
    return await asyncio.to_thread(build, "calendar", "v3", credentials=creds)


async def list_events(db: UserDB, timezone: str, days: int = 1) -> list[dict[str, Any]]:
    service = await _get_service(db)
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days)).isoformat()

    def _fetch():
        return (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime",
                timeZone=timezone,
            )
            .execute()
        )

    result = await asyncio.to_thread(_fetch)
    events = []
    for ev in result.get("items", []):
        start = ev["start"].get("dateTime", ev["start"].get("date", ""))
        end = ev["end"].get("dateTime", ev["end"].get("date", ""))
        events.append({
            "id": ev["id"],
            "summary": ev.get("summary", "(no title)"),
            "start": start,
            "end": end,
            "location": ev.get("location", ""),
        })
    return events


async def create_event(
    db: UserDB,
    timezone: str,
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
) -> dict[str, Any]:
    service = await _get_service(db)
    body: dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location

    def _create():
        return service.events().insert(calendarId="primary", body=body).execute()

    event = await asyncio.to_thread(_create)
    return {"id": event["id"], "summary": event.get("summary", ""), "htmlLink": event.get("htmlLink", "")}


async def update_event(
    db: UserDB,
    timezone: str,
    event_id: str,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    service = await _get_service(db)

    def _get():
        return service.events().get(calendarId="primary", eventId=event_id).execute()

    existing = await asyncio.to_thread(_get)

    if summary is not None:
        existing["summary"] = summary
    if start is not None:
        existing["start"] = {"dateTime": start, "timeZone": timezone}
    if end is not None:
        existing["end"] = {"dateTime": end, "timeZone": timezone}
    if description is not None:
        existing["description"] = description
    if location is not None:
        existing["location"] = location

    def _update():
        return service.events().update(calendarId="primary", eventId=event_id, body=existing).execute()

    event = await asyncio.to_thread(_update)
    return {"id": event["id"], "summary": event.get("summary", ""), "htmlLink": event.get("htmlLink", "")}
