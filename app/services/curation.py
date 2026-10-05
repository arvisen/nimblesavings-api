"""
Curation layer: your editorial tags (age range, seasons, festivals), kept
SEPARATE from live retailer data on purpose.

Why this file exists: once USE_MOCK_DATA=False, bestseller/price/rating/
review/image data comes live from Amazon/Walmart via SerpApi — but those
APIs have no concept of "this fits the Winter season" or "this is a
Christmas gift idea." That's your judgment, and it needs to persist across
refreshes instead of living inside the mock data (which stops being used
once you go live).

Stored as a simple JSON file so it's easy to open and hand-edit without a
database tool. Keyed by product_id (Amazon ASIN / Walmart item ID / etc —
whatever your bestseller source returns as the item's unique identifier).

Workflow once live:
1. Call get_products_needing_curation() after a bestseller refresh — it
   tells you which live product_ids have no entry yet.
2. Look up each one (its title/brand are in the raw bestseller data) and
   add a short entry below with your tags.
3. Re-run — those products now carry your tags going forward.
"""

import json
from pathlib import Path
from typing import Optional

CURATION_FILE = Path(__file__).resolve().parent.parent.parent / "curation.json"

# Seed with entries matching the mock data, so nothing breaks today.
DEFAULT_CURATION: dict[str, dict] = {
    "B0MOCK001": {"age_months_min": 0, "age_months_max": 3, "seasons": ["All-season"], "festivals": ["Baby shower registry"]},
    "B0MOCK002": {"age_months_min": 0, "age_months_max": 3, "seasons": ["All-season"], "festivals": ["Baby shower registry"]},
    "B0MOCK003": {"age_months_min": 0, "age_months_max": 3, "seasons": ["All-season"], "festivals": ["Baby shower registry"]},
    "WMOCK001":  {"age_months_min": 0, "age_months_max": 3, "seasons": ["All-season"], "festivals": ["Baby shower registry"]},
    "B0MOCK010": {"age_months_min": 0, "age_months_max": 5, "seasons": ["All-season"], "festivals": ["Baby shower registry"]},
    "B0MOCK011": {"age_months_min": 0, "age_months_max": 6, "seasons": ["Fall", "Winter"], "festivals": []},
    "B0MOCK020": {"age_months_min": 0, "age_months_max": 18, "seasons": ["All-season"], "festivals": ["Baby shower registry"]},
    "B0MOCK030": {"age_months_min": 12, "age_months_max": 36, "seasons": ["Winter"], "festivals": []},
    "B0MOCK040": {"age_months_min": 12, "age_months_max": 36, "seasons": ["All-season"], "festivals": ["Christmas", "Birthday"]},
    "B0MOCK041": {"age_months_min": 12, "age_months_max": 36, "seasons": ["Fall"], "festivals": ["Halloween"]},
}


def _load() -> dict[str, dict]:
    if not CURATION_FILE.exists():
        _save(DEFAULT_CURATION)
        return DEFAULT_CURATION
    with open(CURATION_FILE, "r") as f:
        return json.load(f)


def _save(data: dict[str, dict]) -> None:
    with open(CURATION_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_curation(product_id: str) -> Optional[dict]:
    """Returns the curation tags for a product_id, or None if not yet tagged."""
    return _load().get(product_id)


def set_curation(
    product_id: str,
    age_months_min: Optional[int] = None,
    age_months_max: Optional[int] = None,
    seasons: Optional[list[str]] = None,
    festivals: Optional[list[str]] = None,
) -> None:
    """Add or update tags for a product. Call this as you curate new live products."""
    data = _load()
    data[product_id] = {
        "age_months_min": age_months_min,
        "age_months_max": age_months_max,
        "seasons": seasons or [],
        "festivals": festivals or [],
    }
    _save(data)


def get_products_needing_curation(raw_items: list[dict]) -> list[dict]:
    """
    Given a list of raw bestseller items (live or mock), returns the ones
    with no curation entry yet — your "to tag" list after each refresh.
    Returns just enough info (id, title, brand) to go look the product up.
    """
    data = _load()
    return [
        {"product_id": i["product_id"], "title": i["title"], "brand": i.get("brand")}
        for i in raw_items
        if i["product_id"] not in data
    ]
