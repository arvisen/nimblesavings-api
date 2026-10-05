"""
Pydantic models shared across the API.
These define the normalized shape we convert every external
data source (Amazon, SerpApi, retailer scrapers, etc.) into.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PriceListing(BaseModel):
    """A single seller's price for a product."""
    seller: str
    price: float
    currency: str = "USD"
    url: str
    in_stock: bool = True
    fetched_at: datetime = datetime.utcnow()


class PromoCode(BaseModel):
    """A discount code available for a seller (storewide or product-specific)."""
    seller: str
    code: str
    discount_type: str  # "percent" | "fixed" | "free_shipping"
    discount_value: float
    min_purchase: Optional[float] = None
    expires_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None


class RecallInfo(BaseModel):
    """CPSC recall flag, attached to a product if found."""
    is_recalled: bool = False
    recall_title: Optional[str] = None
    recall_url: Optional[str] = None
    checked_at: datetime = datetime.utcnow()


class Product(BaseModel):
    """A single bestseller item, with price/promo/recall data attached."""
    product_id: str
    title: str
    brand: Optional[str] = None
    category: str          # e.g. "Feeding" — grouping/menu label
    subcategory: str       # e.g. "Bottles" — the actual shoppable unit
    age_stage: str          # e.g. "Baby & Infant (0-12mo)" — primary browse dimension

    # Precise age range in months, for fine-grained filtering within a stage
    # (e.g. "6-9 months" inside "Infant (3-12mo)"). Optional: falls back to
    # the stage's own range if not set.
    age_months_min: Optional[int] = None
    age_months_max: Optional[int] = None

    # Cross-cutting tags — a product can carry several of each, unlike
    # age_stage/category which are single-value browse buckets.
    seasons: list[str] = []    # e.g. ["Winter"], ["Spring", "Summer"], ["All-season"]
    festivals: list[str] = []  # e.g. ["Christmas", "Birthday"], ["Halloween"]

    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    bestseller_rank: Optional[int] = None
    bestseller_source: str = "Amazon Best Sellers"
    prices: list[PriceListing] = []
    best_price: Optional[PriceListing] = None
    promo_codes: list[PromoCode] = []
    recall: Optional[RecallInfo] = None


class CategoryResponse(BaseModel):
    age_stage: str
    category: str
    subcategory: Optional[str] = None  # None when this is a category-level (aggregated) response
    season: Optional[str] = None      # set when the request filtered by season
    festival: Optional[str] = None    # set when the request filtered by festival
    products: list[Product]
