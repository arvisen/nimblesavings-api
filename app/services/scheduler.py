"""
Background scheduler: the automation described in the README's Stage 3.

Runs inside the same FastAPI process (no separate worker/Redis needed at
this scale) using APScheduler. Two jobs:
- refresh_watched_prices: checks every product currently on someone's
  watchlist, and emails anyone whose target was hit or whose price dropped
  since it was last checked.
- (Bestseller/full-catalog refresh would follow the same pattern — add a
  second job here once you're caching the full catalog, not just watched
  items, per Stage 2/3 in the README.)
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services import watchlist, prices, email_alerts

logger = logging.getLogger("scheduler")

# How often to re-check watched products. Prices don't change hourly for
# most of these categories, so every 6 hours is plenty and keeps SerpApi
# usage (and cost) low. Tighten this once you're on a paid data plan.
CHECK_INTERVAL_HOURS = 6


async def refresh_watched_prices() -> None:
    watches = watchlist.list_all_watches()
    if not watches:
        logger.info("No active watches — skipping price check.")
        return

    logger.info("Checking prices for %d watched item(s)...", len(watches))
    for watch in watches:
        listings = await prices.get_prices_for_product(watch["product_id"], watch["title"])
        if not listings:
            continue

        best = listings[0]  # already sorted cheapest-first
        watchlist.update_seen_price(watch["id"], best.price)

        target = watch.get("target_price")
        last_notified = watch.get("last_notified_price")

        hit_target = target is not None and best.price <= target
        dropped_since_last_notification = (
            last_notified is not None and best.price < last_notified
        )
        # First-ever check with no target set: record a baseline, don't email yet.
        first_check_no_target = target is None and last_notified is None

        if first_check_no_target:
            watchlist.mark_notified(watch["id"], best.price)
            continue

        if hit_target or dropped_since_last_notification:
            email_alerts.send_price_drop_email(
                to_email=watch["email"],
                product_title=watch["title"],
                new_price=best.price,
                seller=best.seller,
                url=best.url,
            )
            watchlist.mark_notified(watch["id"], best.price)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_watched_prices,
        "interval",
        hours=CHECK_INTERVAL_HOURS,
        next_run_time=None,  # first run waits one interval; call manually to test immediately
        id="refresh_watched_prices",
    )
    scheduler.start()
    logger.info("Scheduler started — refreshing watched prices every %sh.", CHECK_INTERVAL_HOURS)
    return scheduler
