"""Google OAuth2 helper for per-user token management."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from ..config import CONFIG
from ..db import UserDB

log = logging.getLogger("dabbar.google_auth")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def build_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CONFIG.google_client_id,
                "client_secret": CONFIG.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=CONFIG.google_redirect_uri,
    )


def get_auth_url(user_id: int) -> str:
    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=str(user_id),
    )
    return auth_url


async def handle_oauth_callback(code: str, user_id: int) -> None:
    flow = build_flow()
    await asyncio.to_thread(flow.fetch_token, code=code)
    creds = flow.credentials
    db = UserDB(CONFIG.data_dir, user_id)
    await db.save_google_tokens({
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    })


async def get_credentials(db: UserDB) -> Credentials | None:
    token_data = await db.get_google_tokens()
    if not token_data:
        return None
    expiry = None
    if token_data.get("expiry"):
        expiry = datetime.fromisoformat(token_data["expiry"])
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
        expiry=expiry,
    )
    if creds.expired and creds.refresh_token:
        await asyncio.to_thread(creds.refresh, Request())
        await db.save_google_tokens({
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or []),
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        })
    return creds
