"""
Affiliate product feed importer.

Some retailers (Snugglebugz, Old Navy via Impact, H&M via whichever network
covers it) don't offer a live "search" API the way Amazon/Walmart do via
SerpApi. Instead, once your affiliate application is approved, they give
you a product feed — a CSV or XML file listing their whole catalog
(title, price, image, stock, your affiliate URL), usually re-downloadable
on a schedule (daily is typical).

This file handles that pattern: download/parse the feed, then match a
feed row to one of YOUR products by title/brand similarity (since the
feed has no knowledge of your internal product_id). Matching is
intentionally simple — a real multi-source product-matching system (UPC/
barcode matching, etc.) is the Stage 4 work mentioned in the README; this
is a lightweight version that's good enough for a single extra retailer.

USE_MOCK_DATA=True uses a small hand-written mock feed so this is testable
with zero real feed file. Flip to False once you have a real feed URL/file
from an approved affiliate program.
"""

import csv
import io
import difflib
from typing import Optional

import httpx

from app.models import PriceListing

USE_MOCK_DATA = True

# One entry per feed-based retailer you've been approved for. FEED_URL is
# wherever that network hosts your downloadable catalog file (Impact,
# Snugglebugz's own affiliate dashboard, etc. — check your approval email).
FEED_CONFIG: dict[str, dict] = {
    "Snugglebugz": {
        "feed_url": "",  # fill in once approved, e.g. "https://.../snugglebugz_feed.csv"
    },
    # "Old Navy": {"feed_url": "..."},  # add once approved via Impact
}

MOCK_FEEDS: dict[str, list[dict]] = {
    "Snugglebugz": [
        {
            "title": "Dr. Brown's Natural Flow Anti-Colic Baby Bottles 8oz 3-Pack",
            "brand": "Dr. Brown's",
            "price": "27.99",
            "url": "https://snugglebugz.ca/products/dr-browns-bottles-3pk",
            "image_url": "https://example.com/img/sb-drbrowns.jpg",
            "in_stock": "true",
        },
        {
            "title": "Columbia Toddler Fleece Snowsuit One Piece",
            "brand": "Columbia",
            "price": "74.99",
            "url": "https://snugglebugz.ca/products/columbia-fleece-snowsuit",
            "image_url": "https://example.com/img/sb-snowsuit.jpg",
            "in_stock": "true",
        },
    ],
}

# Feed cache so we don't re-download/parse on every request within a process.
_feed_cache: dict[str, list[dict]] = {}

# Below this similarity score (0-1), we treat it as "not the same product"
# rather than risk showing the wrong item's price.
MATCH_THRESHOLD = 0.6


def _load_feed(retailer: str) -> list[dict]:
    if retailer in _feed_cache:
        return _feed_cache[retailer]

    if USE_MOCK_DATA:
        rows = MOCK_FEEDS.get(retailer, [])
        _feed_cache[retailer] = rows
        return rows

    config = FEED_CONFIG.get(retailer)
    if not config or not config.get("feed_url"):
        return []

    resp = httpx.get(config["feed_url"], timeout=30)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)
    _feed_cache[retailer] = rows
    return rows


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _find_best_match(title: str, brand: Optional[str], feed_rows: list[dict]) -> Optional[dict]:
    best_row, best_score = None, 0.0
    for row in feed_rows:
        score = _similarity(title, row.get("title", ""))
        # A matching brand name is a strong signal — boost the score rather
        # than requiring an exact one, since brand strings can differ
        # slightly ("Dr. Brown's" vs "Dr Browns") between sources.
        if brand and row.get("brand") and _similarity(brand, row["brand"]) > 0.7:
            score += 0.15
        if score > best_score:
            best_row, best_score = row, score
    return best_row if best_score >= MATCH_THRESHOLD else None


def get_feed_price_listing(
    retailer: str, product_title: str, product_brand: Optional[str] = None
) -> Optional[PriceListing]:
    """
    Returns a PriceListing from this retailer's feed if a confident match
    is found for the given product, else None (most products won't be in
    every small retailer's catalog — that's expected, not an error).
    """
    feed_rows = _load_feed(retailer)
    if not feed_rows:
        return None

    match = _find_best_match(product_title, product_brand, feed_rows)
    if not match:
        return None

    try:
        price = float(match["price"])
    except (KeyError, ValueError):
        return None

    return PriceListing(
        seller=retailer,
        price=price,
        url=match.get("url", ""),
        in_stock=str(match.get("in_stock", "true")).lower() == "true",
    )


def refresh_feed(retailer: str) -> int:
    """Force a re-download/parse on next access. Call this on a schedule
    (e.g. daily, alongside your bestseller/price refresh job) rather than
    relying on the in-process cache forever. Returns rows cached."""
    _feed_cache.pop(retailer, None)
    return len(_load_feed(retailer))
