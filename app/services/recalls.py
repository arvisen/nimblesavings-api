"""
CPSC recall check.

CPSC (Consumer Product Safety Commission) publishes a public, free API —
no key required. Live version queries it by product title/brand keywords.
Docs: https://www.cpsc.gov/Recalls/CPSC-Recalls-API

Kept as a mock here so the endpoint is runnable without network calls;
swap USE_MOCK_DATA to False once you're ready to hit the real API.
"""

import httpx
from datetime import datetime
from app.models import RecallInfo

USE_MOCK_DATA = True

# Hand-picked example: an empty match means "not recalled" for the mock set.
MOCK_RECALLED_KEYWORDS: list[str] = []  # e.g. ["some-recalled-brand-model"]


async def check_recall(title: str, brand: str | None) -> RecallInfo:
    if USE_MOCK_DATA:
        hit = any(kw.lower() in title.lower() for kw in MOCK_RECALLED_KEYWORDS)
        return RecallInfo(is_recalled=hit, checked_at=datetime.utcnow())

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.saferproducts.gov/RestWebServices/Recall",
            params={"ProductName": title, "format": "json"},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            top = results[0]
            return RecallInfo(
                is_recalled=True,
                recall_title=top.get("Title"),
                recall_url=top.get("URL"),
                checked_at=datetime.utcnow(),
            )
        return RecallInfo(is_recalled=False, checked_at=datetime.utcnow())
