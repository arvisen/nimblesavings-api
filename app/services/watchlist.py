"""
Watchlist: parents subscribe an email to a product, optionally with a
target price. The scheduler (scheduler.py) checks these periodically and
triggers an email via email_alerts.py when the price drops.
"""

from typing import Optional
from app.db import get_conn


def add_watch(email: str, product_id: str, title: str, target_price: Optional[float] = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO watchlist (email, product_id, title, target_price) VALUES (?, ?, ?, ?)",
            (email, product_id, title, target_price),
        )
        conn.commit()
        return cur.lastrowid


def list_watches_for_email(email: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE email = ? ORDER BY created_at DESC", (email,)
        ).fetchall()
        return [dict(r) for r in rows]


def list_all_watches() -> list[dict]:
    """Used by the scheduler to know which products need a price check."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM watchlist").fetchall()
        return [dict(r) for r in rows]


def update_seen_price(watch_id: int, price: float) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE watchlist SET last_seen_price = ? WHERE id = ?", (price, watch_id))
        conn.commit()


def mark_notified(watch_id: int, price: float) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE watchlist SET last_notified_price = ? WHERE id = ?", (price, watch_id))
        conn.commit()


def remove_watch(watch_id: int, email: str) -> bool:
    """Requires the email to match, so one person can't delete another's watch."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM watchlist WHERE id = ? AND email = ?", (watch_id, email))
        conn.commit()
        return cur.rowcount > 0
