"""Telegram Stars payment handling."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import (
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from .config import CONFIG
from .db import UserDB

log = logging.getLogger("dabbar.payments")

payments_router = Router()

PREMIUM_TOOLS = {
    "list_events", "create_event", "update_event",
    "list_emails", "read_email", "draft_email", "send_email",
    "add_expense", "list_expenses", "expense_summary",
}

FREE_TOOLS = {
    "add_reminder", "list_reminders",
    "add_task", "list_tasks", "complete_task", "delete_task",
    "web_search", "connect_google",
}


async def check_access(db: UserDB, tool_name: str) -> bool:
    if tool_name in FREE_TOOLS:
        return True
    if await db.is_subscribed():
        return True
    trial_start = await db.get_profile("trial_start")
    if trial_start:
        start = datetime.fromisoformat(trial_start)
        if start.tzinfo is None:
            start = start.replace(tzinfo=ZoneInfo("UTC"))
        if datetime.now(ZoneInfo("UTC")) - start < timedelta(days=CONFIG.free_trial_days):
            return True
    return False


async def start_trial_if_new(db: UserDB) -> None:
    existing = await db.get_profile("trial_start")
    if not existing:
        await db.set_profile("trial_start", datetime.now(ZoneInfo("UTC")).isoformat())


@payments_router.message(Command("subscribe"))
async def on_subscribe(message: Message, bot: Bot) -> None:
    if not message.from_user:
        return
    db = UserDB(CONFIG.data_dir, message.from_user.id)
    if await db.is_subscribed():
        info = await db.get_subscription_info()
        await message.answer(
            f"You're already subscribed!\nExpires: {info['expires_at']}\n\nEnjoy Dabbar!"
        )
        return

    prices = [LabeledPrice(label="Dabbar Monthly", amount=CONFIG.subscription_stars_amount)]
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Dabbar Premium",
        description="Monthly subscription — Calendar, Gmail, voice, expense tracking, and unlimited features.",
        payload=f"sub_{message.from_user.id}",
        currency="XTR",
        prices=prices,
    )


@payments_router.pre_checkout_query()
async def on_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@payments_router.message(lambda m: m.successful_payment is not None)
async def on_successful_payment(message: Message) -> None:
    if not message.from_user or not message.successful_payment:
        return
    payment = message.successful_payment
    db = UserDB(CONFIG.data_dir, message.from_user.id)
    expires = (datetime.now(ZoneInfo("UTC")) + timedelta(days=30)).isoformat()
    await db.add_subscription(
        telegram_charge_id=payment.telegram_payment_charge_id,
        provider_charge_id=payment.provider_payment_charge_id,
        amount=payment.total_amount,
        expires_at=expires,
    )
    await message.answer(
        "Payment received! Your Dabbar Premium subscription is now active for 30 days.\n\n"
        "Enjoy Calendar, Gmail, voice messages, and all premium features!"
    )
