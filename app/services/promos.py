"""
Promo code source.

For now this is a hand-seeded table (Stage 1, as discussed) — the realistic
starting point before plugging into an affiliate network feed (CJ, Rakuten,
Awin, Skimlinks) in a later stage.
"""

from datetime import datetime, timedelta
from app.models import PromoCode

# Seed a small manual table of storewide codes. In production this would be
# its own DB table, refreshed by whatever feed/process you choose later.
SEEDED_PROMO_CODES: dict[str, list[dict]] = {
    "Target": [
        {
            "code": "BABY10",
            "discount_type": "percent",
            "discount_value": 10,
            "min_purchase": 50,
        }
    ],
    "Walmart": [
        {
            "code": "FREESHIP",
            "discount_type": "free_shipping",
            "discount_value": 0,
            "min_purchase": 35,
        }
    ],
}


def get_promo_codes_for_seller(seller: str) -> list[PromoCode]:
    raw = SEEDED_PROMO_CODES.get(seller, [])
    now = datetime.utcnow()
    return [
        PromoCode(
            seller=seller,
            code=item["code"],
            discount_type=item["discount_type"],
            discount_value=item["discount_value"],
            min_purchase=item.get("min_purchase"),
            expires_at=now + timedelta(days=30),
            verified_at=now,
        )
        for item in raw
    ]
