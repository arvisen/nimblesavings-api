from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import products, watchlist
from app.db import init_db
from app.services.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Baby Essentials Price Compare API",
    description="Bestsellers by age stage/category, with price comparison, "
    "promo codes, promo/recall checks, and price-drop alerts.",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow the WordPress frontend (any origin, for now — tighten before launch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(watchlist.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "try": "/products/Newborn (0-3mo)/Feeding",
        "docs": "/docs",
    }
