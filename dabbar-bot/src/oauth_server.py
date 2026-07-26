"""Minimal aiohttp server for Google OAuth callbacks and waitlist API."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

from .config import CONFIG
from .tools.google_auth import handle_oauth_callback

log = logging.getLogger("dabbar.oauth")

_bot_instance = None


async def oauth_callback(request: web.Request) -> web.Response:
    code = request.query.get("code")
    state = request.query.get("state", "")
    if not code or not state.isdigit():
        return web.Response(text="Missing code or invalid state.", status=400)
    user_id = int(state)
    try:
        await handle_oauth_callback(code, user_id)
        if _bot_instance:
            await _bot_instance.send_message(
                user_id,
                "Connected! You can now use calendar and email features.\n\n"
                "Try: _show my calendar for today_ or _check my inbox_",
                parse_mode="Markdown",
            )
        return web.Response(
            text="<html><body><h2>Connected! You can close this tab and return to Telegram.</h2></body></html>",
            content_type="text/html",
        )
    except Exception as e:
        log.exception("OAuth callback failed for user %s", user_id)
        return web.Response(text=f"OAuth failed: {e}", status=500)


async def waitlist_submit(request: web.Request) -> web.Response:
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=headers)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400, headers=headers)

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    phone = str(data.get("phone", "")).strip()
    if not email:
        return web.json_response({"error": "Email is required"}, status=400, headers=headers)

    entry = {
        "name": name,
        "email": email,
        "phone": phone,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "website",
    }
    waitlist_file = CONFIG.data_dir / "waitlist.jsonl"
    with open(waitlist_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    log.info("Waitlist signup: %s <%s>", name, email)

    if _bot_instance and CONFIG.admin_id:
        try:
            await _bot_instance.send_message(
                CONFIG.admin_id,
                f"New waitlist signup!\n\nName: {name}\nEmail: {email}\nPhone: {phone or 'N/A'}",
            )
        except Exception:
            pass

    return web.json_response({"ok": True, "message": "You're on the list!"}, headers=headers)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/oauth/callback", oauth_callback)
    app.router.add_post("/waitlist", waitlist_submit)
    app.router.add_options("/waitlist", waitlist_submit)
    return app


async def start_oauth_server(bot) -> web.AppRunner:
    global _bot_instance
    _bot_instance = bot
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", CONFIG.oauth_server_port)
    await site.start()
    log.info("OAuth/waitlist server listening on port %s", CONFIG.oauth_server_port)
    return runner
