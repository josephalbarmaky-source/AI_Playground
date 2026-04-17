"""Expense tracking tool functions."""
from __future__ import annotations

from typing import Any

from ..db import UserDB

EXPENSE_CATEGORIES = [
    "food", "transport", "shopping", "bills", "entertainment",
    "health", "education", "groceries", "fuel", "other",
]


async def add_expense(
    db: UserDB,
    amount: float,
    category: str,
    description: str = "",
    currency: str = "AED",
    receipt_file_id: str | None = None,
) -> dict[str, Any]:
    category = category.lower().strip()
    if category not in EXPENSE_CATEGORIES:
        category = "other"
    eid = await db.add_expense(amount, category, description, currency, receipt_file_id)
    return {"id": eid, "amount": amount, "category": category, "currency": currency}


async def list_expenses(
    db: UserDB, limit: int = 20, category: str | None = None
) -> list[dict[str, Any]]:
    return await db.list_expenses(limit=limit, category=category)


async def expense_summary(db: UserDB, days: int = 30) -> list[dict[str, Any]]:
    return await db.expense_summary(days=days)
