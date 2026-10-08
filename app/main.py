import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import products, watchlist
from app.db import init_db
from app.services.scheduler import start_scheduler


def _env_flag(name: str) -> bool:
    """Off unless the environment variable is set to true/1/yes."""
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


# Price alerts aren't live: the watchlist routes have no ownership check (any email's
# list can be read, added to or deleted). Keep them, and the price-check scheduler that
# only serves them, switched off unless WATCHLIST_ENABLED=true.
WATCHLIST_ENABLED = _env_flag("WATCHLIST_ENABLED")

# Internal tools (e.g. /needs-curation) stay off unless INTERNAL_ROUTES_ENABLED=true.
INTERNAL_ROUTES_ENABLED = _env_flag("INTERNAL_ROUTES_ENABLED")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler() if WATCHLIST_ENABLED else None
    yield
    if scheduler:
        scheduler.shutdown()


app = FastAPI(
    title="Baby Essentials Price Compare API",
    description="Bestsellers by age stage/category, with price comparison, "
    "promo codes, promo/recall checks, and price-drop alerts.",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow the WordPress frontend (apex and www domains only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nimblesavings.com", "https://www.nimblesavings.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
if INTERNAL_ROUTES_ENABLED:
    app.include_router(products.internal_router)
if WATCHLIST_ENABLED:
    app.include_router(watchlist.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "try": "/products/Baby & Infant (0-12mo)/Feeding",
        "docs": "/docs",
    }
