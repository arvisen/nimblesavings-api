from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import Product, CategoryResponse
from app.services import bestsellers, prices, promos, recalls, taxonomy, curation, category_structure

router = APIRouter(prefix="/products", tags=["products"])

# Internal tools, mounted only when INTERNAL_ROUTES_ENABLED=true (see main.py).
internal_router = APIRouter(prefix="/products", tags=["internal"])

# Minimum review count a product needs before its own rating is trusted at
# full weight. Below this, its score gets pulled toward the category
# average — same idea as IMDB's "Top 250" weighted rating, so a brand-new
# item with a couple of 5-star reviews can't outrank an established
# bestseller with thousands of slightly-lower-rated reviews.
MIN_REVIEWS_FOR_FULL_WEIGHT = 50


def _weighted_score(all_products: list[Product], product: Product) -> float:
    """
    Bayesian-style blended score: weighted_score = (v / (v+m)) * R + (m / (v+m)) * C
    where v = this product's review count, R = its rating, m = the minimum-
    reviews threshold above, and C = the average rating across this result
    set (computed dynamically so it adapts per category rather than using
    one hardcoded baseline).
    """
    rated = [p.rating for p in all_products if p.rating is not None]
    category_avg = sum(rated) / len(rated) if rated else 4.5  # fallback if nothing rated yet

    v = product.review_count or 0
    r = product.rating or category_avg
    m = MIN_REVIEWS_FOR_FULL_WEIGHT

    return (v / (v + m)) * r + (m / (v + m)) * category_avg


async def _build_response(
    age_stage: str,
    category: str,
    subcategory: Optional[str],
    raw_items: list[dict],
    season: Optional[str],
    festival: Optional[str],
    age_months: Optional[int],
    sort_by: str,
) -> CategoryResponse:
    """Shared enrichment/filtering/sorting, used by both the subcategory-level
    and category-aggregate endpoints below."""

    if not raw_items:
        raise HTTPException(
            status_code=404,
            detail=f"No bestseller data for stage='{age_stage}', category='{category}'"
            + (f", subcategory='{subcategory}'" if subcategory else "")
            + ". Check spelling/spacing matches a seeded key.",
        )

    # Merge in your curation tags (age range/seasons/festivals) — see
    # curation.py for why this is a separate layer from retailer data.
    for item in raw_items:
        tags = curation.get_curation(item["product_id"])
        if tags:
            item.setdefault("age_months_min", tags.get("age_months_min"))
            item.setdefault("age_months_max", tags.get("age_months_max"))
            item.setdefault("seasons", tags.get("seasons", []))
            item.setdefault("festivals", tags.get("festivals", []))

    if season:
        raw_items = [
            i for i in raw_items
            if any(s.lower() == season.lower() for s in i.get("seasons", []))
        ]
    if festival:
        raw_items = [
            i for i in raw_items
            if any(f.lower() == festival.lower() for f in i.get("festivals", []))
        ]
    if age_months is not None:
        raw_items = [
            i for i in raw_items
            if i.get("age_months_min") is None
            or (i["age_months_min"] <= age_months <= i.get("age_months_max", 999))
        ]

    if not raw_items:
        raise HTTPException(
            status_code=404,
            detail="No products match this stage/category with the given "
            "season/festival/age_months filters.",
        )

    products: list[Product] = []
    for item in raw_items:
        listings = await prices.get_prices_for_product(
            item["product_id"], item["title"], item.get("brand")
        )
        best = listings[0] if listings else None

        promo_codes = []
        if best:
            promo_codes = promos.get_promo_codes_for_seller(best.seller)

        recall_info = await recalls.check_recall(item["title"], item.get("brand"))

        products.append(
            Product(
                product_id=item["product_id"],
                title=item["title"],
                brand=item.get("brand"),
                category=item.get("category", category),
                subcategory=item.get("subcategory", subcategory or ""),
                age_stage=age_stage,
                age_months_min=item.get("age_months_min"),
                age_months_max=item.get("age_months_max"),
                seasons=item.get("seasons", []),
                festivals=item.get("festivals", []),
                image_url=item.get("image_url"),
                rating=item.get("rating"),
                review_count=item.get("review_count"),
                bestseller_rank=item.get("bestseller_rank"),
                bestseller_source=item.get("bestseller_source", "Amazon Best Sellers"),
                prices=listings,
                best_price=best,
                promo_codes=promo_codes,
                recall=recall_info,
            )
        )

    if sort_by == "reviews":
        products.sort(key=lambda p: (-(p.review_count or 0), -(p.rating or 0)))
    elif sort_by == "score":
        products.sort(key=lambda p: -_weighted_score(products, p))
    else:
        products.sort(key=lambda p: (p.bestseller_rank or 999))

    return CategoryResponse(
        age_stage=age_stage, category=category, subcategory=subcategory,
        season=season, festival=festival, products=products,
    )


@router.get("/taxonomy/festivals")
async def get_festivals(region: str = Query("CA", description="Region code, e.g. 'CA'")):
    """
    Returns the festival/occasion tags configured for a region, so the
    frontend can render filter chips dynamically rather than hardcoding
    a list that may not fit every region's audience.
    """
    festivals = taxonomy.get_festivals_for_region(region)
    if not festivals:
        raise HTTPException(status_code=404, detail=f"No festival list configured for region '{region}' yet.")
    return {"region": region.upper(), "festivals": festivals}


@router.get("/taxonomy/tree")
async def get_taxonomy_tree():
    """
    Returns the full age_stage -> category -> [subcategory] structure.
    Use this to build WordPress nav menus / taxonomy terms rather than
    hardcoding the list twice.
    """
    return category_structure.get_full_tree()


@internal_router.get("/{age_stage}/{category}/{subcategory}/needs-curation")
async def get_subcategory_needing_curation(age_stage: str, category: str, subcategory: str):
    """Run after refreshing live bestsellers to see which products in this
    subcategory have no age/season/festival tags yet."""
    raw_items = await bestsellers.get_bestsellers(age_stage, category, subcategory)
    return {"untagged_products": curation.get_products_needing_curation(raw_items)}


@router.get("/{age_stage}/{category}/{subcategory}", response_model=CategoryResponse)
async def get_subcategory_products(
    age_stage: str,
    category: str,
    subcategory: str,
    season: Optional[str] = Query(None, description="Optional filter, e.g. 'Winter'. Case-insensitive."),
    festival: Optional[str] = Query(None, description="Optional filter, e.g. 'Christmas'. Case-insensitive."),
    age_months: Optional[int] = Query(None, description="Optional filter: child's exact age in months."),
    sort_by: str = Query(
        "bestseller",
        description="'bestseller' (default), 'reviews', or 'score' (blended rating+reviews).",
    ),
):
    """
    Returns bestsellers for one specific subcategory (the real shoppable
    unit — e.g. "Bottles"), each enriched with current prices, promo
    codes, and a recall check.

    Example: GET /products/Baby & Infant (0-12mo)/Feeding/Bottles
    """
    raw_items = await bestsellers.get_bestsellers(age_stage, category, subcategory)
    return await _build_response(
        age_stage, category, subcategory, raw_items, season, festival, age_months, sort_by
    )


@router.get("/{age_stage}/{category}", response_model=CategoryResponse)
async def get_category_products(
    age_stage: str,
    category: str,
    season: Optional[str] = Query(None, description="Optional filter, e.g. 'Winter'. Case-insensitive."),
    festival: Optional[str] = Query(None, description="Optional filter, e.g. 'Christmas'. Case-insensitive."),
    age_months: Optional[int] = Query(None, description="Optional filter: child's exact age in months."),
    sort_by: str = Query(
        "bestseller",
        description="'bestseller' (default), 'reviews', or 'score' (blended rating+reviews).",
    ),
):
    """
    Category-level AGGREGATE: combines every subcategory under this
    category (per category_structure.py) into one list — this is what
    powers a "Feeding essentials" style checklist page spanning Bottles,
    Bibs, High Chair, etc. all at once, rather than one specific product
    type.

    Example: GET /products/Baby & Infant (0-12mo)/Feeding
    """
    raw_items = await bestsellers.get_bestsellers_for_category(age_stage, category)
    return await _build_response(
        age_stage, category, None, raw_items, season, festival, age_months, sort_by
    )
