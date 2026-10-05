"""
Price comparison source.

Mirrors the same USE_MOCK_DATA pattern as bestsellers.py.
Live version would call SerpApi's Google Shopping engine (search by
product title/UPC) and normalize each result into a PriceListing.
Docs: https://serpapi.com/google-shopping-api

Also merges in any FEED_RETAILERS — retailers without a live query API
(Snugglebugz, Old Navy via Impact, etc.) whose prices come from a
downloaded catalog feed instead. See affiliate_feeds.py for that side.
"""

import os
import random
from datetime import datetime
from typing import Optional

from app.models import PriceListing
from app.services import affiliate_feeds

USE_MOCK_DATA = True
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

MOCK_SELLERS = ["Amazon", "Target", "Walmart", "BuyBuy Baby"]

# Retailers priced via affiliate_feeds.py instead of a live API call. Add a
# name here once you've been approved and configured it in FEED_CONFIG —
# every product comparison will then also check that retailer's feed for
# a matching item.
FEED_RETAILERS = ["Snugglebugz"]


async def get_prices_for_product(
    product_id: str, title: str, brand: Optional[str] = None
) -> list[PriceListing]:
    listings: list[PriceListing] = []

    if USE_MOCK_DATA:
        base = round(random.uniform(15, 120), 2)
        for seller in random.sample(MOCK_SELLERS, k=3):
            variance = round(base * random.uniform(-0.15, 0.1), 2)
            listings.append(
                PriceListing(
                    seller=seller,
                    price=round(base + variance, 2),
                    url=f"https://example.com/{seller.lower().replace(' ', '')}/{product_id}",
                    in_stock=random.random() > 0.1,
                    fetched_at=datetime.utcnow(),
                )
            )
    else:
        # Live version (sketch):
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     resp = await client.get("https://serpapi.com/search", params={
        #         "engine": "google_shopping",
        #         "q": title,
        #         "api_key": SERPAPI_KEY,
        #     })
        #     results = resp.json().get("shopping_results", [])
        #     listings = [PriceListing(seller=r["source"], price=r["extracted_price"],
        #                               url=r["link"]) for r in results]
        pass

    # Check every feed-based retailer for a matching product. Most won't
    # have a match for most products — that's expected (a specialty baby
    # retailer won't stock everything Amazon does), not an error.
    for retailer in FEED_RETAILERS:
        feed_listing = affiliate_feeds.get_feed_price_listing(retailer, title, brand)
        if feed_listing:
            listings.append(feed_listing)

    return sorted(listings, key=lambda p: p.price)
