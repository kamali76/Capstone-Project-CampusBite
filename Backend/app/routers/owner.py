"""Restaurant-owner endpoints: menu, orders, delivery assignment, returns, stats, reminders."""
import math
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..constants import (
    NON_REVENUE_STATUSES,
    OWNER_SETTABLE,
    OrderStatus,
    PaymentStatus,
    ReturnStatus,
    Role,
)
from ..database import get_db
from ..models import (
    AdminReminderLog,
    MenuItem,
    Order,
    OrderItem,
    Restaurant,
    ReturnRequest,
    Review,
    User,
    utcnow,
)
from ..schemas import (
    AssignIn,
    AvailabilityIn,
    MenuItemIn,
    MenuItemOut,
    OrderOut,
    OrderPage,
    OwnerReturnOut,
    OwnerReturnPage,
    OwnerStatusIn,
    ReminderOut,
    RestaurantOut,
    RestaurantUpdate,
    ReturnDecisionIn,
    StatsOut,
    TopItem,
    UserMini,
)
from ..security import require_roles
from ..services.orders import (
    ORDER_LOAD,
    OrderFilters,
    PageParams,
    apply_order_filters,
    apply_transition,
    get_order_or_404,
    paginate_orders,
    record_refund,
)
from ..services.reminders import generate_reminders

router = APIRouter(prefix="/owner", tags=["Restaurant owner"])

owner_only = require_roles(Role.OWNER)


def get_my_restaurant(
    db: Session = Depends(get_db), owner: User = Depends(owner_only)
) -> Restaurant:
    restaurant = db.scalar(select(Restaurant).where(Restaurant.owner_id == owner.id))
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No restaurant is linked to this account")
    return restaurant


# ---------------------------------------------------------------- restaurant
@router.get("/restaurant", response_model=RestaurantOut)
def my_restaurant(db: Session = Depends(get_db), restaurant: Restaurant = Depends(get_my_restaurant)):
    avg, count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.restaurant_id == restaurant.id
        )
    ).one()
    return RestaurantOut(
        id=restaurant.id,
        name=restaurant.name,
        cuisine=restaurant.cuisine,
        description=restaurant.description,
        address=restaurant.address,
        rating=round(float(avg), 1) if avg is not None else None,
        review_count=count,
    )


@router.put("/restaurant", response_model=RestaurantOut)
def update_restaurant(
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    restaurant.name = payload.name
    restaurant.cuisine = payload.cuisine
    restaurant.description = payload.description
    restaurant.address = payload.address
    db.commit()
    return my_restaurant(db, restaurant)


# ---------------------------------------------------------------- menu
def _get_my_item(db: Session, restaurant: Restaurant, item_id: int) -> MenuItem:
    item = db.scalar(
        select(MenuItem).where(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id)
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu item not found")
    return item


@router.get("/menu-items", response_model=list[MenuItemOut])
def list_my_menu(
    db: Session = Depends(get_db), restaurant: Restaurant = Depends(get_my_restaurant)
):
    return db.scalars(
        select(MenuItem)
        .where(MenuItem.restaurant_id == restaurant.id)
        .order_by(MenuItem.category, MenuItem.name)
    ).all()


@router.post("/menu-items", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
def add_menu_item(
    payload: MenuItemIn,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    item = MenuItem(restaurant_id=restaurant.id, **payload.model_dump())
    db.add(item)
    db.commit()
    return item


@router.put("/menu-items/{item_id}", response_model=MenuItemOut)
def update_menu_item(
    item_id: int,
    payload: MenuItemIn,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    item = _get_my_item(db, restaurant, item_id)
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    return item


@router.patch("/menu-items/{item_id}/availability", response_model=MenuItemOut)
def set_availability(
    item_id: int,
    payload: AvailabilityIn,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    item = _get_my_item(db, restaurant, item_id)
    item.is_available = payload.is_available
    db.commit()
    return item


@router.delete("/menu-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    item = _get_my_item(db, restaurant, item_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- orders
@router.get("/orders", response_model=OrderPage)
def list_restaurant_orders(
    filters: OrderFilters = Depends(),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    base = apply_order_filters(select(Order).where(Order.restaurant_id == restaurant.id), filters)
    return paginate_orders(db, base, params)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OwnerStatusIn,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    if payload.status not in OWNER_SETTABLE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Owners can set ACCEPTED, PREPARING or READY here. "
            "Use the assign endpoint for ASSIGNED and the returns endpoint for refunds.",
        )
    order = get_order_or_404(db, order_id, restaurant_id=restaurant.id)
    apply_transition(order, payload.status, Role.OWNER)
    db.commit()
    return get_order_or_404(db, order.id)


@router.get("/delivery-partners", response_model=list[UserMini])
def list_delivery_partners(
    db: Session = Depends(get_db), _owner: User = Depends(owner_only)
):
    return db.scalars(
        select(User).where(User.role == Role.DELIVERY).order_by(User.name)
    ).all()


@router.post("/orders/{order_id}/assign", response_model=OrderOut)
def assign_delivery_partner(
    order_id: int,
    payload: AssignIn,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    order = get_order_or_404(db, order_id, restaurant_id=restaurant.id)
    partner = db.get(User, payload.delivery_partner_id)
    if partner is None or partner.role != Role.DELIVERY:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Delivery partner not found")
    if order.status != OrderStatus.READY:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"A delivery partner can only be assigned when the order is READY (it is {order.status})",
        )
    apply_transition(order, OrderStatus.ASSIGNED, Role.OWNER)
    order.delivery_partner_id = partner.id
    db.commit()
    return get_order_or_404(db, order.id)


# ---------------------------------------------------------------- returns / refunds
@router.get("/returns", response_model=OwnerReturnPage)
def list_returns(
    status_filter: str | None = Query(None, alias="status"),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    base = (
        select(ReturnRequest)
        .join(Order, Order.id == ReturnRequest.order_id)
        .where(Order.restaurant_id == restaurant.id)
    )
    if status_filter:
        base = base.where(ReturnRequest.status == status_filter)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.options(selectinload(ReturnRequest.order).options(*ORDER_LOAD))
        .order_by(ReturnRequest.created_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    ).all()
    return OwnerReturnPage(
        items=[OwnerReturnOut.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=max(1, math.ceil(total / params.page_size)),
    )


@router.patch("/returns/{return_id}", response_model=OwnerReturnOut)
def decide_return(
    return_id: int,
    payload: ReturnDecisionIn,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    request = db.scalar(
        select(ReturnRequest)
        .join(Order, Order.id == ReturnRequest.order_id)
        .where(ReturnRequest.id == return_id, Order.restaurant_id == restaurant.id)
    )
    if request is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Return request not found")
    if request.status != ReturnStatus.REQUESTED:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"This request was already {request.status}"
        )

    order = get_order_or_404(db, request.order_id, restaurant_id=restaurant.id)
    request.decided_at = utcnow()
    if payload.decision == "approve":
        apply_transition(order, OrderStatus.REFUNDED, Role.OWNER)
        record_refund(db, order, f"Return approved: {request.reason[:150]}")
        order.payment_status = PaymentStatus.REFUNDED
        request.status = ReturnStatus.APPROVED
        order.return_status = ReturnStatus.APPROVED
    else:
        request.status = ReturnStatus.REJECTED
        order.return_status = ReturnStatus.REJECTED
        order.updated_at = utcnow()
    db.commit()

    fresh = db.scalar(
        select(ReturnRequest)
        .where(ReturnRequest.id == request.id)
        .options(selectinload(ReturnRequest.order).options(*ORDER_LOAD))
    )
    return OwnerReturnOut.model_validate(fresh)


# ---------------------------------------------------------------- stats & reminders
@router.get("/stats", response_model=StatsOut)
def restaurant_stats(
    tz_offset: int = Query(0, ge=-840, le=840, description="Client minutes ahead of UTC"),
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_my_restaurant),
):
    rid = restaurant.id
    by_status = dict(
        db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.restaurant_id == rid)
            .group_by(Order.status)
        ).all()
    )
    total_orders = sum(by_status.values())

    shift = timedelta(minutes=tz_offset)
    local_today = (utcnow() + shift).date()
    today_start = datetime.combine(local_today, time.min) - shift  # local midnight in UTC
    orders_today = db.scalar(
        select(func.count(Order.id)).where(
            Order.restaurant_id == rid, Order.created_at >= today_start
        )
    )

    revenue_orders, revenue = db.execute(
        select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0.0)).where(
            Order.restaurant_id == rid, Order.status.notin_(NON_REVENUE_STATUSES)
        )
    ).one()

    top_rows = db.execute(
        select(OrderItem.name, func.sum(OrderItem.quantity).label("qty"))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.restaurant_id == rid, Order.status.notin_(NON_REVENUE_STATUSES))
        .group_by(OrderItem.name)
        .order_by(func.sum(OrderItem.quantity).desc(), OrderItem.name)
        .limit(5)
    ).all()

    avg_rating, review_count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.restaurant_id == rid)
    ).one()

    pending_returns = db.scalar(
        select(func.count(ReturnRequest.id))
        .join(Order, Order.id == ReturnRequest.order_id)
        .where(Order.restaurant_id == rid, ReturnRequest.status == ReturnStatus.REQUESTED)
    )

    generate_reminders(db, restaurant_id=rid)
    active_reminders = len(_pending_reminders(db, rid))

    return StatsOut(
        total_orders=total_orders,
        orders_today=orders_today or 0,
        revenue=round(float(revenue), 2),
        average_order_value=round(float(revenue) / revenue_orders, 2) if revenue_orders else 0.0,
        orders_by_status=by_status,
        top_items=[TopItem(name=n, quantity=int(q)) for n, q in top_rows],
        average_rating=round(float(avg_rating), 1) if avg_rating is not None else None,
        review_count=review_count,
        pending_returns=pending_returns or 0,
        active_reminders=active_reminders,
    )


def _pending_reminders(db: Session, restaurant_id: int) -> list[AdminReminderLog]:
    """Reminders whose order is still sitting in the status that triggered them."""
    rows = db.scalars(
        select(AdminReminderLog)
        .where(AdminReminderLog.restaurant_id == restaurant_id)
        .options(selectinload(AdminReminderLog.order))
        .order_by(AdminReminderLog.created_at.desc())
    ).all()
    return [r for r in rows if r.order.status == r.status_at_time]


@router.get("/reminders", response_model=list[ReminderOut])
def list_reminders(
    db: Session = Depends(get_db), restaurant: Restaurant = Depends(get_my_restaurant)
):
    # Run the check now so the dashboard is current without waiting for the background loop
    generate_reminders(db, restaurant_id=restaurant.id)
    return [
        ReminderOut(
            id=r.id,
            order_id=r.order_id,
            status_at_time=r.status_at_time,
            message=r.message,
            created_at=r.created_at,
            still_pending=True,
        )
        for r in _pending_reminders(db, restaurant.id)
    ]
