"""Dabbar Telegram bot — main entry point.

Run:
    python -m src.bot
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from .config import CONFIG
from .db import UserDB
from .dispatcher import dispatch
from .llm import OllamaClient, parse_tool_call
from .oauth_server import start_oauth_server
from .payments import PREMIUM_TOOLS, check_access, payments_router, start_trial_if_new
from .tools.google_auth import get_auth_url
from .tools.transcribe import transcribe_voice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dabbar")

WELCOME_EN = (
    "👋 Hello, I'm *Dabbar* (دبّر) — your personal AI assistant.\n\n"
    "I can:\n"
    "• Set reminders & manage to-do lists\n"
    "• Manage your Google Calendar & Gmail\n"
    "• Track your expenses\n"
    "• Search the web\n"
    "• Understand voice messages\n"
    "• Chat in Arabic or English\n\n"
    "Commands: /connect (Google) · /subscribe (Premium) · /status · /reset\n\n"
    "Try: _remind me to call Ahmad in 10 minutes_\n"
    "Or:  _what's on my calendar today?_"
)

WELCOME_AR = (
    "👋 أهلاً، أنا *دبّر* — مساعدك الشخصي بالذكاء الاصطناعي.\n\n"
    "بقدر:\n"
    "• أحط لك تذكيرات وأدير قائمة مهامك\n"
    "• أدير تقويم جوجل وإيميلك\n"
    "• أتتبع مصاريفك\n"
    "• أبحث لك بالإنترنت\n"
    "• أفهم الرسائل الصوتية\n"
    "• أحكي معك عربي أو إنجليزي\n\n"
    "الأوامر: /connect (جوجل) · /subscribe (اشتراك) · /status · /reset\n\n"
    "جرب: _ذكرني أتصل بأحمد بعد ١٠ دقايق_"
)


def make_bot() -> Bot:
    return Bot(token=CONFIG.telegram_token, parse_mode=ParseMode.MARKDOWN)


async def send_reminder(bot: Bot, chat_id: int, reminder_id: int, text: str, db: UserDB) -> None:
    try:
        await bot.send_message(chat_id, f"⏰ *Reminder:* {text}")
        await db.mark_reminder_fired(reminder_id)
    except Exception as e:  # noqa: BLE001
        log.exception("Failed to send reminder %s: %s", reminder_id, e)


def build_schedule_callback(bot: Bot, scheduler: AsyncIOScheduler, chat_id: int, db: UserDB):
    """Return a sync callback that arms a reminder job."""
    def _schedule(reminder_id: int, fire_at_utc: datetime, text: str) -> None:
        scheduler.add_job(
            send_reminder,
            trigger=DateTrigger(run_date=fire_at_utc),
            args=[bot, chat_id, reminder_id, text, db],
            id=f"rem-{chat_id}-{reminder_id}",
            replace_existing=True,
        )
    return _schedule


async def handle_user_message(
    message: Message,
    bot: Bot,
    scheduler: AsyncIOScheduler,
    llm: OllamaClient,
) -> None:
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    db = UserDB(CONFIG.data_dir, user_id)
    await start_trial_if_new(db)
    history = await db.recent_messages(limit=12)

    response = await llm.chat(history, message.text)
    tool_call = parse_tool_call(response)

    if tool_call:
        if tool_call["tool"] in PREMIUM_TOOLS:
            has_access = await check_access(db, tool_call["tool"])
            if not has_access:
                await message.answer(
                    "🔒 This feature requires a Dabbar Premium subscription.\n\n"
                    "Send /subscribe to get started.\n"
                    "Free trial expired."
                )
                return

        schedule_cb = build_schedule_callback(bot, scheduler, message.chat.id, db)
        result = await dispatch(
            tool_call["tool"],
            tool_call.get("args", {}),
            db=db,
            timezone=CONFIG.timezone,
            schedule_reminder_cb=schedule_cb,
        )
        await message.answer(result)
        await db.add_message("user", message.text)
        await db.add_message("assistant", result)
    else:
        await message.answer(response or "…")
        await db.add_message("user", message.text)
        await db.add_message("assistant", response)


async def restore_pending_reminders(bot: Bot, scheduler: AsyncIOScheduler) -> None:
    """On startup, re-arm reminders that haven't fired yet."""
    if not CONFIG.data_dir.exists():
        return
    for db_file in CONFIG.data_dir.glob("user_*.db"):
        try:
            user_id = int(db_file.stem.replace("user_", ""))
        except ValueError:
            continue
        db = UserDB(CONFIG.data_dir, user_id)
        rems = await db.list_reminders()
        for r in rems:
            fire_at = datetime.fromisoformat(r["fire_at"])
            if fire_at <= datetime.now(ZoneInfo("UTC")):
                # Overdue — fire once immediately
                await send_reminder(bot, user_id, r["id"], r["text"], db)
                continue
            scheduler.add_job(
                send_reminder,
                trigger=DateTrigger(run_date=fire_at),
                args=[bot, user_id, r["id"], r["text"], db],
                id=f"rem-{user_id}-{r['id']}",
                replace_existing=True,
            )


async def main() -> None:
    bot = make_bot()
    dp = Dispatcher()
    scheduler = AsyncIOScheduler(timezone="UTC")
    llm = OllamaClient(CONFIG.ollama_host, CONFIG.model_main, CONFIG.model_fast)

    @dp.message(CommandStart())
    async def on_start(message: Message) -> None:
        text = WELCOME_AR if _is_arabic(message.text or "") else WELCOME_EN
        await message.answer(text)

    @dp.message(Command("reset"))
    async def on_reset(message: Message) -> None:
        if not message.from_user:
            return
        db = UserDB(CONFIG.data_dir, message.from_user.id)
        await db.clear_messages()
        await message.answer("🧹 Conversation history cleared.")

    @dp.message(Command("connect"))
    async def on_connect(message: Message) -> None:
        if not message.from_user:
            return
        if not CONFIG.google_client_id:
            await message.answer("Google integration is not configured.")
            return
        url = get_auth_url(message.from_user.id)
        await message.answer(
            f"🔗 To connect your Google Calendar & Gmail, click below:\n\n{url}\n\n"
            "After authorizing, return here and I'll confirm the connection.",
        )

    @dp.message(Command("status"))
    async def on_status(message: Message) -> None:
        if not message.from_user:
            return
        db = UserDB(CONFIG.data_dir, message.from_user.id)
        sub = await db.get_subscription_info()
        google = await db.get_google_tokens()
        lines = ["📊 *Your Dabbar Status*\n"]
        if sub:
            lines.append(f"💎 Subscription: Active (expires {sub['expires_at'][:10]})")
        else:
            trial = await db.get_profile("trial_start")
            if trial:
                from datetime import timedelta
                start = datetime.fromisoformat(trial)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=ZoneInfo("UTC"))
                remaining = CONFIG.free_trial_days - (datetime.now(ZoneInfo("UTC")) - start).days
                if remaining > 0:
                    lines.append(f"🆓 Free trial: {remaining} days remaining")
                else:
                    lines.append("❌ Free trial expired. Send /subscribe")
            else:
                lines.append("🆓 Free trial: not started yet")
        lines.append(f"🔗 Google: {'Connected' if google else 'Not connected (/connect)'}")
        await message.answer("\n".join(lines))

    @dp.message(Command("waitlist"))
    async def on_waitlist(message: Message) -> None:
        if not message.from_user or message.from_user.id != CONFIG.admin_id:
            await message.answer("Admin only.")
            return
        import json as _json
        waitlist_file = CONFIG.data_dir / "waitlist.jsonl"
        if not waitlist_file.exists():
            await message.answer("No signups yet.")
            return
        lines_raw = waitlist_file.read_text().strip().split("\n")
        total = len(lines_raw)
        recent = []
        for line in lines_raw[-5:]:
            entry = _json.loads(line)
            recent.append(f"  • {entry['name']} <{entry['email']}> ({entry['timestamp'][:10]})")
        text = f"📋 Waitlist: {total} total signups\n\nRecent:\n" + "\n".join(recent)
        await message.answer(text)

    dp.include_router(payments_router)

    @dp.message(F.voice)
    async def on_voice(message: Message) -> None:
        if not message.from_user or not message.voice:
            return
        try:
            file = await bot.get_file(message.voice.file_id)
            file_bytes = await bot.download_file(file.file_path)
            audio_data = file_bytes.read()
            text = await transcribe_voice(audio_data)
            if not text:
                await message.answer("🎙️ Sorry, I couldn't understand the voice message. Could you type it instead?")
                return
            await message.answer(f"🎙️ _\"{text}\"_\n\nProcessing...")
            message.text = text
            await handle_user_message(message, bot, scheduler, llm)
        except Exception as e:
            log.exception("Voice handling error")
            await message.answer(f"⚠️ Voice processing error: {e}")

    @dp.message(F.photo)
    async def on_photo(message: Message) -> None:
        if not message.from_user or not message.photo:
            return
        try:
            photo = message.photo[-1]
            caption = message.caption or ""
            prompt = (
                f"The user sent a photo"
                + (f" with caption: \"{caption}\"" if caption else "")
                + ". If this appears to be a receipt or expense, extract the amount and category "
                + "and call add_expense. If it's not a receipt, reply normally."
            )
            db = UserDB(CONFIG.data_dir, message.from_user.id)
            response = await llm.chat(await db.recent_messages(limit=6), prompt)
            tool_call = parse_tool_call(response)
            if tool_call:
                if tool_call["tool"] == "add_expense":
                    tool_call["args"]["receipt_file_id"] = photo.file_id
                schedule_cb = build_schedule_callback(bot, scheduler, message.chat.id, db)
                result = await dispatch(
                    tool_call["tool"], tool_call.get("args", {}),
                    db=db, timezone=CONFIG.timezone,
                    schedule_reminder_cb=schedule_cb,
                )
                await message.answer(result)
            else:
                await message.answer(response or "I see the photo, but I'm not sure what to do with it.")
        except Exception as e:
            log.exception("Photo handling error")
            await message.answer(f"⚠️ Error processing photo: {e}")

    @dp.message(F.text)
    async def on_text(message: Message) -> None:
        try:
            await handle_user_message(message, bot, scheduler, llm)
        except Exception as e:  # noqa: BLE001
            log.exception("Error handling message")
            await message.answer(f"⚠️ Something went wrong: {e}")

    scheduler.start()
    await restore_pending_reminders(bot, scheduler)

    oauth_runner = None
    if CONFIG.google_client_id:
        oauth_runner = await start_oauth_server(bot)

    log.info("Dabbar is online.")
    try:
        await dp.start_polling(bot)
    finally:
        if oauth_runner:
            await oauth_runner.cleanup()
        await llm.close()
        await bot.session.close()
        scheduler.shutdown(wait=False)


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06ff" for ch in text)


if __name__ == "__main__":
    asyncio.run(main())
