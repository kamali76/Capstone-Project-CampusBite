from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MenuItem, Restaurant, Review, User
from ..schemas import MenuItemOut, RestaurantOut
from ..security import get_current_user

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


def _rating_map(db: Session) -> dict[int, tuple[float, int]]:
    rows = db.execute(
        select(Review.restaurant_id, func.avg(Review.rating), func.count(Review.id)).group_by(
            Review.restaurant_id
        )
    ).all()
    return {rid: (round(float(avg), 1), count) for rid, avg, count in rows}


def _to_out(restaurant: Restaurant, ratings: dict) -> RestaurantOut:
    avg, count = ratings.get(restaurant.id, (None, 0))
    return RestaurantOut(
        id=restaurant.id,
        name=restaurant.name,
        cuisine=restaurant.cuisine,
        description=restaurant.description,
        address=restaurant.address,
        rating=avg,
        review_count=count,
    )


@router.get("", response_model=list[RestaurantOut])
def list_restaurants(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    restaurants = db.scalars(
        select(Restaurant).where(Restaurant.is_active.is_(True)).order_by(Restaurant.name)
    ).all()
    ratings = _rating_map(db)
    return [_to_out(r, ratings) for r in restaurants]


def _get_active_restaurant(db: Session, restaurant_id: int) -> Restaurant:
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None or not restaurant.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(
    restaurant_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
):
    return _to_out(_get_active_restaurant(db, restaurant_id), _rating_map(db))


@router.get("/{restaurant_id}/menu", response_model=list[MenuItemOut])
def get_menu(
    restaurant_id: int,
    search: str | None = Query(None, max_length=100),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    _get_active_restaurant(db, restaurant_id)
    stmt = select(MenuItem).where(MenuItem.restaurant_id == restaurant_id)
    if search and search.strip():
        stmt = stmt.where(MenuItem.name.ilike(f"%{search.strip()}%"))
    if min_price is not None:
        stmt = stmt.where(MenuItem.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(MenuItem.price <= max_price)
    return db.scalars(stmt.order_by(MenuItem.category, MenuItem.name)).all()
