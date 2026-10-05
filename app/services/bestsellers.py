"""
Bestseller data source — now multi-retailer.

"Bestseller" is inherently retailer-specific: Amazon's top sellers in a
category and Walmart's top sellers in that same category are two different,
real rankings, not the same list. So rather than pick one retailer as THE
source of truth, this file pulls each configured retailer's own bestseller
list for a given (age_stage, category) and merges them into one combined
list, each item tagged with which retailer's ranking it came from
(`bestseller_source`). Price comparison across ALL retailers (prices.py)
still runs for every item regardless of which retailer it was discovered
through — that part was already multi-retailer.

USE_MOCK_DATA=True returns hand-written sample data so the API is
runnable/demoable with zero API keys.

To go live: set USE_MOCK_DATA=False and fill in SERPAPI_KEY (get one at
serpapi.com).
- Amazon: SerpApi's Amazon Best Sellers engine, by browse node ID.
  Docs: https://serpapi.com/amazon-best-sellers
- Walmart: SerpApi's Walmart engine, sorted by best-seller/top-rated, by
  category ID or search query.
  Docs: https://serpapi.com/walmart-search-api

NOTE ON PRODUCT MATCHING: this does NOT attempt to detect "same physical
product on both Amazon and Walmart" and merge them into one card — that's
real product-matching work (fuzzy title/brand/UPC matching), deliberately
deferred to a later stage per the README's roadmap. For now, the same
product may legitimately appear twice, once per retailer's own ranking —
that's expected, not a bug, until that matching logic is built.

KEYING: as of the category/subcategory restructure, everything here is
keyed by (age_stage, category, subcategory) — subcategory is the real
shoppable unit (e.g. "Bottles"), category is just a grouping label (e.g.
"Feeding") used for navigation and for aggregating several subcategories
into one checklist page. See category_structure.py for the full tree.
Newborn (0-3mo) and Infant (3-12mo) have been merged into one stage,
"Baby & Infant (0-12mo)".
"""

import os
import httpx

USE_MOCK_DATA = True
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# Which retailers to pull bestsellers from, and that retailer's category
# identifier, per (age_stage, category, subcategory). Add a retailer key
# here (and a matching branch below) to bring in more sources later.
# This is seeded for a handful of subcategories to demonstrate the
# pattern — follow the same shape to fill in the rest of the tree in
# category_structure.py.
SOURCE_CONFIG: dict[tuple[str, str, str], dict[str, str]] = {
    ("Baby & Infant (0-12mo)", "Feeding", "Bottles"): {
        "amazon": "165799011",     # Amazon browse node ID
        "walmart": "baby bottles",  # Walmart search/category term
    },
    ("Baby & Infant (0-12mo)", "Sleeping", "Bassinet"): {
        "amazon": "165798011",
        "walmart": "baby sleep bassinet",
    },
    ("Baby & Infant (0-12mo)", "Health & Safety", "Baby Thermometer"): {
        "amazon": "165801011",
        "walmart": "baby monitor",
    },
}

MOCK_PRODUCTS = {
    ("Baby & Infant (0-12mo)", "Feeding", "Bottles"): [
        {
            "product_id": "B0MOCK001",
            "title": "Dr. Brown's Natural Flow Anti-Colic Baby Bottles, 8oz (3-Pack)",
            "brand": "Dr. Brown's",
            "rating": 4.8,
            "review_count": 42310,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/drbrowns.jpg",
            "age_months_min": 0,
            "age_months_max": 12,
            "seasons": ["All-season"],
            "festivals": ["Baby shower registry"],
        },
        {
            "product_id": "B0MOCK002",
            "title": "Philips Avent Natural Baby Bottle Newborn Starter Set",
            "brand": "Philips Avent",
            "rating": 4.7,
            "review_count": 28904,
            "bestseller_rank": 2,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/avent.jpg",
            "age_months_min": 0,
            "age_months_max": 12,
            "seasons": ["All-season"],
            "festivals": ["Baby shower registry"],
        },
        {
            "product_id": "WMOCK001",
            "title": "Parent's Choice Advanced Infant Formula",
            "brand": "Parent's Choice",
            "rating": 4.6,
            "review_count": 5210,
            "bestseller_rank": 1,
            "bestseller_source": "Walmart Top Sellers",
            "image_url": "https://example.com/img/parentschoice.jpg",
            "age_months_min": 0,
            "age_months_max": 12,
            "seasons": ["All-season"],
            "festivals": ["Baby shower registry"],
        },
    ],
    ("Baby & Infant (0-12mo)", "Feeding", "Breast Pump"): [
        {
            "product_id": "B0MOCK003",
            "title": "Haakaa Manual Breast Pump Silicone",
            "brand": "Haakaa",
            "rating": 4.7,
            "review_count": 61532,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/haakaa.jpg",
            "age_months_min": 0,
            "age_months_max": 12,
            "seasons": ["All-season"],
            "festivals": ["Baby shower registry"],
        },
    ],
    ("Baby & Infant (0-12mo)", "Sleeping", "Bassinet"): [
        {
            "product_id": "B0MOCK010",
            "title": "HALO BassiNest Swivel Sleeper Bassinet",
            "brand": "HALO",
            "rating": 4.6,
            "review_count": 15220,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/halo.jpg",
            "age_months_min": 0,
            "age_months_max": 5,
            "seasons": ["All-season"],
            "festivals": ["Baby shower registry"],
        },
    ],
    ("Baby & Infant (0-12mo)", "Sleeping", "Swaddle"): [
        {
            "product_id": "B0MOCK011",
            "title": "HALO SleepSack Swaddle, 100% Cotton",
            "brand": "HALO",
            "rating": 4.8,
            "review_count": 33110,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/sleepsack.jpg",
            "age_months_min": 0,
            "age_months_max": 6,
            "seasons": ["Fall", "Winter"],
            "festivals": [],
        },
    ],
    ("Baby & Infant (0-12mo)", "Health & Safety", "Baby Thermometer"): [
        {
            "product_id": "B0MOCK020",
            "title": "Owlet Dream Sock Baby Monitor",
            "brand": "Owlet",
            "rating": 4.3,
            "review_count": 8021,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/owlet.jpg",
            "age_months_min": 0,
            "age_months_max": 18,
            "seasons": ["All-season"],
            "festivals": ["Baby shower registry"],
        },
    ],
    ("Toddler (1-3yr)", "Clothing", "Outerwear"): [
        {
            "product_id": "B0MOCK030",
            "title": "Columbia Toddler Fleece Snowsuit",
            "brand": "Columbia",
            "rating": 4.7,
            "review_count": 3980,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/snowsuit.jpg",
            "age_months_min": 12,
            "age_months_max": 36,
            "seasons": ["Winter"],
            "festivals": [],
        },
    ],
    ("Toddler (1-3yr)", "Playing", "Outdoor Play"): [
        {
            "product_id": "B0MOCK040",
            "title": "Melissa & Doug Wooden Shape Sorting Cube",
            "brand": "Melissa & Doug",
            "rating": 4.8,
            "review_count": 21044,
            "bestseller_rank": 1,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/shapecube.jpg",
            "age_months_min": 12,
            "age_months_max": 36,
            "seasons": ["All-season"],
            "festivals": ["Christmas", "Birthday"],
        },
        {
            "product_id": "B0MOCK041",
            "title": "Toddler Pumpkin Halloween Costume, Plush",
            "brand": "Old Navy",
            "rating": 4.5,
            "review_count": 1870,
            "bestseller_rank": 2,
            "bestseller_source": "Amazon Best Sellers",
            "image_url": "https://example.com/img/pumpkincostume.jpg",
            "age_months_min": 12,
            "age_months_max": 36,
            "seasons": ["Fall"],
            "festivals": ["Halloween"],
        },
    ],
}


async def get_bestsellers(age_stage: str, category: str, subcategory: str) -> list[dict]:
    """
    Returns a merged list of raw bestseller dicts for a given
    stage/category/subcategory, combining every retailer configured for it
    in SOURCE_CONFIG. Each item carries `bestseller_source` saying which
    retailer's ranking it came from.
    """
    if USE_MOCK_DATA:
        items = MOCK_PRODUCTS.get((age_stage, category, subcategory), [])
    else:
        sources = SOURCE_CONFIG.get((age_stage, category, subcategory))
        if not sources:
            return []

        items = []
        async with httpx.AsyncClient() as client:
            if "amazon" in sources:
                items.extend(await _fetch_amazon_bestsellers(client, sources["amazon"]))
            if "walmart" in sources:
                items.extend(await _fetch_walmart_bestsellers(client, sources["walmart"]))
            # Add more retailers here the same way (e.g. "wellca") once you
            # have a working source for them.

    for item in items:
        item.setdefault("category", category)
        item.setdefault("subcategory", subcategory)
    return items


async def get_bestsellers_for_category(age_stage: str, category: str) -> list[dict]:
    """
    Aggregates every subcategory under a category into one combined list —
    this is what powers a "Feeding essentials" style checklist page that
    spans Bottles, Bibs, High Chair, etc. all at once.
    """
    from app.services import category_structure

    subcategories = category_structure.get_subcategories(age_stage, category)
    merged: list[dict] = []
    for sub in subcategories:
        merged.extend(await get_bestsellers(age_stage, category, sub))
    return merged


async def _fetch_amazon_bestsellers(client: httpx.AsyncClient, node_id: str) -> list[dict]:
    resp = await client.get(
        "https://serpapi.com/search",
        params={
            "engine": "amazon_bestsellers",  # verify exact engine name in SerpApi docs
            "node": node_id,
            "amazon_domain": "amazon.ca",
            "api_key": SERPAPI_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    # NOTE: adjust this key/field mapping once you inspect a real response —
    # exact field names vary by engine version.
    items = data.get("bestsellers", [])
    for item in items:
        item["bestseller_source"] = "Amazon Best Sellers"
    return items


async def _fetch_walmart_bestsellers(client: httpx.AsyncClient, query: str) -> list[dict]:
    resp = await client.get(
        "https://serpapi.com/search",
        params={
            "engine": "walmart",
            "query": query,
            "sort": "best_seller",  # verify exact sort param name in SerpApi docs
            "api_key": SERPAPI_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    # NOTE: adjust this key/field mapping once you inspect a real response.
    items = data.get("organic_results", [])
    for item in items:
        item["bestseller_source"] = "Walmart Top Sellers"
    return items
