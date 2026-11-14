"""Order business logic: state machine, payments, refunds, query helpers."""
import math
import uuid
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql import Select

from ..constants import ALL_STATUSES, TRANSITIONS, OrderStatus, PaymentStatus, ReturnStatus
from ..models import MenuItem, Order, OrderItem, PaymentLedger, Restaurant, utcnow
from ..schemas import OrderCreate

# Eager-load everything an OrderOut needs, so listing orders doesn't trigger N+1 queries.
ORDER_LOAD = (
    joinedload(Order.restaurant),
    joinedload(Order.customer),
    joinedload(Order.delivery_partner),
    joinedload(Order.review),
    joinedload(Order.return_request),
    selectinload(Order.items),
    selectinload(Order.payments),
)


class PageParams:
    """Query parameters shared by every paginated endpoint."""

    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
    ):
        self.page = page
        self.page_size = page_size


class OrderFilters:
    """Optional status/date filters used by customer and owner order lists."""

    def __init__(
        self,
        status: str | None = Query(None, description="Filter by order status"),
        date_from: date | None = Query(None, description="YYYY-MM-DD, inclusive"),
        date_to: date | None = Query(None, description="YYYY-MM-DD, inclusive"),
        tz_offset: int = Query(
            0, ge=-840, le=840,
            description="Client's minutes ahead of UTC (IST = 330) so dates mean local days",
        ),
    ):
        if status is not None and status not in ALL_STATUSES:
            raise HTTPException(422, f"Unknown status '{status}'")
        if date_from and date_to and date_from > date_to:
            raise HTTPException(422, "date_from must not be after date_to")
        self.status = status
        self.date_from = date_from
        self.date_to = date_to
        self.tz_offset = tz_offset


def apply_order_filters(stmt: Select, filters: OrderFilters) -> Select:
    if filters.status:
        stmt = stmt.where(Order.status == filters.status)
    shift = timedelta(minutes=filters.tz_offset)  # local midnight -> UTC
    if filters.date_from:
        stmt = stmt.where(
            Order.created_at >= datetime.combine(filters.date_from, time.min) - shift
        )
    if filters.date_to:
        stmt = stmt.where(
            Order.created_at
            < datetime.combine(filters.date_to + timedelta(days=1), time.min) - shift
        )
    return stmt


def paginate_orders(db: Session, base: Select, params: PageParams) -> dict:
    """`base` is a filtered `select(Order)`; adds count, ordering, paging and eager loads."""
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.options(*ORDER_LOAD)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    ).all()
    return {
        "items": rows,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": max(1, math.ceil(total / params.page_size)),
    }


def get_order_or_404(db: Session, order_id: int, **owner_filter) -> Order:
    """Load an order, restricted by an ownership filter, e.g. customer_id=5.

    Returns 404 (not 403) for orders that belong to someone else, so ids can't be probed.
    """
    stmt = select(Order).where(Order.id == order_id).options(*ORDER_LOAD)
    for column, value in owner_filter.items():
        stmt = stmt.where(getattr(Order, column) == value)
    order = db.scalar(stmt)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def apply_transition(order: Order, new_status: str, actor_role: str) -> None:
    """Move an order to `new_status` if the state machine allows it for `actor_role`."""
    allowed = TRANSITIONS.get(order.status, {})
    if new_status not in allowed:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Invalid status change: {order.status} -> {new_status}",
        )
    if allowed[new_status] != actor_role:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Your role cannot move an order from {order.status} to {new_status}",
        )
    order.status = new_status
    order.updated_at = utcnow()


def record_payment(db: Session, order: Order) -> None:
    """Dummy payment: no gateway, just a ledger row and a mock_paid status."""
    db.add(
        PaymentLedger(
            order=order,
            entry_type="payment",
            amount=order.total_amount,
            status="completed",
            reference=f"MOCK-PAY-{uuid.uuid4().hex[:10].upper()}",
            note="Dummy payment",
        )
    )
    order.payment_status = PaymentStatus.MOCK_PAID


def record_refund(db: Session, order: Order, note: str) -> None:
    db.add(
        PaymentLedger(
            order=order,
            entry_type="refund",
            amount=order.total_amount,
            status="completed",
            reference=f"MOCK-REF-{uuid.uuid4().hex[:10].upper()}",
            note=note,
        )
    )
    order.payment_status = PaymentStatus.REFUNDED


def create_order(db: Session, customer_id: int, payload: OrderCreate) -> Order:
    restaurant = db.get(Restaurant, payload.restaurant_id)
    if restaurant is None or not restaurant.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Restaurant not found")

    # Merge duplicate lines for the same dish
    quantities: dict[int, int] = {}
    for line in payload.items:
        quantities[line.menu_item_id] = quantities.get(line.menu_item_id, 0) + line.quantity

    menu_items = db.scalars(
        select(MenuItem).where(
            MenuItem.id.in_(quantities), MenuItem.restaurant_id == restaurant.id
        )
    ).all()
    found = {m.id: m for m in menu_items}

    for item_id in quantities:
        item = found.get(item_id)
        if item is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Menu item {item_id} does not belong to this restaurant",
            )
        if not item.is_available:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"'{item.name}' is currently unavailable"
            )
        if quantities[item_id] > 50:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Quantity too large")

    # Price is always calculated on the server, never taken from the client
    total = round(sum(found[i].price * q for i, q in quantities.items()), 2)

    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant.id,
        status=OrderStatus.PLACED,
        total_amount=total,
        delivery_address=payload.delivery_address.strip(),
        return_status=ReturnStatus.NONE,
    )
    for item_id, qty in quantities.items():
        item = found[item_id]
        order.items.append(
            OrderItem(
                menu_item_id=item.id, name=item.name, unit_price=item.price, quantity=qty
            )
        )
    db.add(order)
    record_payment(db, order)
    db.commit()
    return get_order_or_404(db, order.id)
