# Baby Essentials Price Compare API — Stage 1 Scaffold

## Taxonomy structure (age_stage > category > subcategory)

Three levels, each with a distinct job:
- **age_stage** — top navigation (e.g. "Baby & Infant (0-12mo)", "Toddler
  (1-3yr)", "Preschool (3-5yr)", "Big Kid (5-12yr)"). Newborn and Infant
  were merged into one combined stage since their essentials overlap
  heavily.
- **category** — a grouping/menu label (e.g. "Feeding"). Not itself a
  bestseller source — it's what aggregates several subcategories into one
  "Feeding essentials" checklist page.
- **subcategory** — the real shoppable unit (e.g. "Bottles"). This is
  what has an actual Amazon browse node / Walmart search term behind it
  in `bestsellers.py`'s `SOURCE_CONFIG`.

See `app/services/category_structure.py` for the full tree and
`GET /products/taxonomy/tree` to fetch it programmatically (e.g. for
building WordPress nav menus/taxonomy terms from the same source of
truth, instead of maintaining the list twice).

Two endpoint shapes:
- `GET /products/{age_stage}/{category}/{subcategory}` — one specific
  product type, e.g. `/products/Baby & Infant (0-12mo)/Feeding/Bottles`
- `GET /products/{age_stage}/{category}` — aggregates every subcategory
  under that category into one combined list, e.g.
  `/products/Baby & Infant (0-12mo)/Feeding` (Bottles + Breast Pump +
  Bibs + ... all together) — this is what a checklist page uses.


A working FastAPI backend that returns bestseller baby products for a given
age stage + category, each enriched with:
- Current prices across mock sellers (sorted cheapest-first)
- Applicable promo codes
- A CPSC recall check

Everything runs on **mock data by default** — no API keys needed to try it.

## Run it locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive API docs, or try:

```
GET http://127.0.0.1:8000/products/Newborn (0-3mo)/Feeding
```

(URL-encode the space, or just click through the /docs UI.)

## Project structure

```
app/
  main.py                 - FastAPI app + CORS setup
  models.py                - Product, PriceListing, PromoCode, RecallInfo
  routers/
    products.py             - GET /products/{age_stage}/{category}
  services/
    bestsellers.py           - bestseller data (mock now, SerpApi/Amazon later)
    prices.py                 - price comparison (mock now, SerpApi Google Shopping later)
    promos.py                  - promo codes (hand-seeded now, affiliate feed later)
    recalls.py                  - CPSC recall check (mock now, free public CPSC API later)
```

## Going from mock to live data

Each service file has `USE_MOCK_DATA = True` at the top and a commented-out
or documented live implementation below it. To go live:

1. **Bestsellers**: sign up at serpapi.com, set `SERPAPI_KEY` env var, flip
   `USE_MOCK_DATA = False` in `bestsellers.py`. Fill in real identifiers in
   `SOURCE_CONFIG` per retailer: Amazon browse node IDs (find by browsing
   Amazon.ca and reading the `node=` parameter in the URL) and Walmart
   search terms/category IDs. Bestsellers are pulled from every retailer
   configured for a given stage/category and merged into one list, each
   item tagged with `bestseller_source` saying which retailer's own
   ranking it came from — "bestseller" is retailer-specific, there's no
   single universal list across stores. Add more retailers by adding a
   branch in `bestsellers.py` the same way. Note: this does not yet merge
   "same physical product on two retailers" into one card — that's
   product-matching work, deferred to Stage 4 below.
2. **Prices**: same SerpApi key covers Google Shopping — flip the flag in
   `prices.py`.
3. **Promo codes**: replace the hand-seeded dict in `promos.py` with a real
   database table, fed by an affiliate network (CJ, Rakuten, Awin, Skimlinks)
   once you've signed up for one.
4. **Recalls**: CPSC's API is free and requires no key — flip the flag in
   `recalls.py` and it works immediately.

## Price-drop alerts (new)

Parents can subscribe an email to a product's price:

```
POST /watchlist   {"email": "...", "product_id": "...", "title": "...", "target_price": 25}
GET  /watchlist?email=...
DELETE /watchlist/{id}?email=...
```

A background job (`app/services/scheduler.py`, using APScheduler) runs
every 6 hours automatically while the app is running — no manual trigger
needed. For each watched product it re-checks the price and emails the
subscriber (via `email_alerts.py`, currently logging instead of sending —
flip `USE_MOCK_DATA` there once you have a Postmark/SendGrid key) when
either the target price is hit or the price has dropped since the last
alert. `CHECK_INTERVAL_HOURS` in that file controls the frequency.

Watchlist data is stored in a local SQLite file (`babyprice.db`, created
automatically) — no separate database server needed at this scale.

## Feed-based retailers (Snugglebugz, Old Navy, etc.)

Some retailers don't offer a live query API like Amazon/Walmart via
SerpApi — instead, once your affiliate application is approved, they give
you a downloadable product catalog feed (CSV/XML). `app/services/
affiliate_feeds.py` handles this pattern: download/parse the feed, then
fuzzy-match a feed row to one of your products by title/brand similarity
(since the feed doesn't know your internal product IDs).

To add a real retailer once approved:
1. Add its name + `feed_url` to `FEED_CONFIG` in `affiliate_feeds.py`.
2. Add its name to `FEED_RETAILERS` in `prices.py`.
3. Flip `USE_MOCK_DATA = False` in `affiliate_feeds.py`.
4. Call `affiliate_feeds.refresh_feed("RetailerName")` on a schedule
   (e.g. daily, alongside your other refresh jobs) so the cached feed
   doesn't go stale.

Matching is intentionally simple (text similarity, not UPC/barcode
matching) — good enough for one or two extra retailers, but a known
limitation: a confident-but-wrong match is possible on similarly-named
products. `MATCH_THRESHOLD` controls how strict it is.

## Next steps (per the staged plan)

- **Stage 2**: swap the in-memory mock calls for a Postgres-backed cache
  (store `products`/`prices`/`promo_codes` tables, avoid re-fetching on
  every request).
- **Stage 3**: add a scheduled job (APScheduler) to refresh bestsellers/
  prices periodically instead of live-fetching per request.
- **Stage 4**: add more sources beyond Amazon (Target, Walmart) and a
  product-matching function to merge listings of the same item.
- **Stage 5**: connect to WordPress — either have WordPress call this API
  directly from the frontend, or write a small script that pushes this data
  into WordPress custom post types via the WP REST API.
- **User accounts + watchlist + price-drop email alerts**: new `users` and
  `watchlist` tables, plus a check inside the Stage 3 scheduled job that
  compares new prices against each watchlist entry and triggers an email
  (SendGrid/Postmark) on a drop.
