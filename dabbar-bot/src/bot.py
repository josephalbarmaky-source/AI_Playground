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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dabbar")

WELCOME_EN = (
    "👋 Hello, I'm *Dabbar* (دبّر) — your personal AI assistant.\n\n"
    "I can:\n"
    "• Set reminders\n"
    "• Manage your to-do list\n"
    "• Search the web\n"
    "• Chat in Arabic or English\n\n"
    "Try: _remind me to call Ahmad in 10 minutes_\n"
    "Or:  _add milk to my list_"
)

WELCOME_AR = (
    "👋 أهلاً، أنا *دبّر* — مساعدك الشخصي بالذكاء الاصطناعي.\n\n"
    "بقدر:\n"
    "• أحط لك تذكيرات\n"
    "• أدير قائمة مهامك\n"
    "• أبحث لك بالإنترنت\n"
    "• أحكي معك عربي أو إنجليزي\n\n"
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
    history = await db.recent_messages(limit=12)

    # First pass: let the LLM decide whether to call a tool
    response = await llm.chat(history, message.text)
    tool_call = parse_tool_call(response)

    if tool_call:
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

    @dp.message(F.text)
    async def on_text(message: Message) -> None:
        try:
            await handle_user_message(message, bot, scheduler, llm)
        except Exception as e:  # noqa: BLE001
            log.exception("Error handling message")
            await message.answer(f"⚠️ Something went wrong: {e}")

    scheduler.start()
    await restore_pending_reminders(bot, scheduler)

    log.info("Dabbar is online.")
    try:
        await dp.start_polling(bot)
    finally:
        await llm.close()
        await bot.session.close()
        scheduler.shutdown(wait=False)


def _is_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06ff" for ch in text)


if __name__ == "__main__":
    asyncio.run(main())
