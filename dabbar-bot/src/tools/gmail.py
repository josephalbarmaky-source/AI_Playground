"""Gmail tool functions."""
from __future__ import annotations

import asyncio
import base64
from email.mime.text import MIMEText
from typing import Any

from googleapiclient.discovery import build

from ..db import UserDB
from .google_auth import get_credentials


async def _get_service(db: UserDB):
    creds = await get_credentials(db)
    if not creds:
        raise RuntimeError("Google account not connected. Send /connect to link your account.")
    return await asyncio.to_thread(build, "gmail", "v1", credentials=creds)


async def list_emails(db: UserDB, max_results: int = 10, query: str = "is:inbox") -> list[dict[str, Any]]:
    service = await _get_service(db)

    def _fetch():
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            emails.append({
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", ""),
            })
        return emails

    return await asyncio.to_thread(_fetch)


async def read_email(db: UserDB, email_id: str) -> dict[str, Any]:
    service = await _get_service(db)

    def _fetch():
        detail = service.users().messages().get(userId="me", id=email_id, format="full").execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        body = ""
        payload = detail.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
        elif payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        return {
            "id": email_id,
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": body[:2000],
        }

    return await asyncio.to_thread(_fetch)


async def draft_email(db: UserDB, to: str, subject: str, body: str) -> dict[str, Any]:
    service = await _get_service(db)
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    def _create():
        return service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()

    draft = await asyncio.to_thread(_create)
    return {"id": draft["id"], "message": f"Draft created: {subject}"}


async def send_email(db: UserDB, to: str, subject: str, body: str) -> dict[str, Any]:
    service = await _get_service(db)
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    def _send():
        return service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

    result = await asyncio.to_thread(_send)
    return {"id": result["id"], "message": f"Email sent to {to}"}
