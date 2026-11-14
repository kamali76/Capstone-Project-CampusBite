"""Delivery-partner endpoints. A partner only ever sees orders assigned to them."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constants import DELIVERY_SETTABLE, OrderStatus, Role
from ..database import get_db
from ..models import Order, User
from ..schemas import DeliveryStatusIn, OrderOut, OrderPage
from ..security import require_roles
from ..services.orders import (
    PageParams,
    apply_transition,
    get_order_or_404,
    paginate_orders,
)

router = APIRouter(prefix="/delivery", tags=["Delivery partner"])

delivery_only = require_roles(Role.DELIVERY)

ACTIVE = (OrderStatus.ASSIGNED, OrderStatus.OUT_FOR_DELIVERY)
HISTORY = (OrderStatus.DELIVERED, OrderStatus.REFUNDED)


@router.get("/orders", response_model=OrderPage)
def list_active_deliveries(
    status_filter: str | None = Query(None, alias="status"),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    partner: User = Depends(delivery_only),
):
    if status_filter is not None and status_filter not in ACTIVE:
        raise HTTPException(422, f"status must be one of {', '.join(ACTIVE)}")
    base = select(Order).where(
        Order.delivery_partner_id == partner.id,
        Order.status.in_([status_filter] if status_filter else ACTIVE),
    )
    return paginate_orders(db, base, params)


@router.get("/history", response_model=OrderPage)
def delivery_history(
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    partner: User = Depends(delivery_only),
):
    base = select(Order).where(
        Order.delivery_partner_id == partner.id, Order.status.in_(HISTORY)
    )
    return paginate_orders(db, base, params)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def update_delivery_status(
    order_id: int,
    payload: DeliveryStatusIn,
    db: Session = Depends(get_db),
    partner: User = Depends(delivery_only),
):
    if payload.status not in DELIVERY_SETTABLE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Delivery partners can only set OUT_FOR_DELIVERY or DELIVERED",
        )
    order = get_order_or_404(db, order_id, delivery_partner_id=partner.id)
    apply_transition(order, payload.status, Role.DELIVERY)
    db.commit()
    return get_order_or_404(db, order.id)
