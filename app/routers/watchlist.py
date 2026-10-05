from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException

from app.services import watchlist

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class AddWatchRequest(BaseModel):
    email: EmailStr
    product_id: str
    title: str
    target_price: Optional[float] = None  # None = alert on any price drop


@router.post("")
def add_to_watchlist(req: AddWatchRequest):
    """Subscribe an email to price-drop alerts for a product."""
    watch_id = watchlist.add_watch(req.email, req.product_id, req.title, req.target_price)
    return {"id": watch_id, "message": "Added. You'll get an email if the price drops."}


@router.get("")
def get_watchlist(email: EmailStr):
    """List everything a given email is watching."""
    return {"email": email, "watches": watchlist.list_watches_for_email(email)}


@router.delete("/{watch_id}")
def delete_from_watchlist(watch_id: int, email: EmailStr):
    """Remove a watch. email must match the one it was created with."""
    removed = watchlist.remove_watch(watch_id, email)
    if not removed:
        raise HTTPException(status_code=404, detail="No matching watch found for that id/email.")
    return {"message": "Removed."}
