"""Customer-facing order endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..constants import OrderStatus, ReturnStatus, Role
from ..database import get_db
from ..models import Order, Review, ReturnRequest, User
from ..schemas import OrderCreate, OrderOut, OrderPage, ReturnIn, ReturnOut, ReviewIn, ReviewOut
from ..security import require_roles
from ..services.orders import (
    OrderFilters,
    PageParams,
    apply_order_filters,
    apply_transition,
    create_order,
    get_order_or_404,
    paginate_orders,
    record_refund,
)

router = APIRouter(prefix="/orders", tags=["Orders (customer)"])

customer_only = require_roles(Role.CUSTOMER)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    customer: User = Depends(customer_only),
):
    return create_order(db, customer.id, payload)


@router.get("", response_model=OrderPage)
def list_my_orders(
    filters: OrderFilters = Depends(),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    customer: User = Depends(customer_only),
):
    base = apply_order_filters(select(Order).where(Order.customer_id == customer.id), filters)
    return paginate_orders(db, base, params)


@router.get("/{order_id}", response_model=OrderOut)
def get_my_order(
    order_id: int, db: Session = Depends(get_db), customer: User = Depends(customer_only)
):
    return get_order_or_404(db, order_id, customer_id=customer.id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int, db: Session = Depends(get_db), customer: User = Depends(customer_only)
):
    order = get_order_or_404(db, order_id, customer_id=customer.id)
    if order.status != OrderStatus.PLACED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Orders can only be cancelled while PLACED (this order is {order.status})",
        )
    apply_transition(order, OrderStatus.CANCELLED, Role.CUSTOMER)
    record_refund(db, order, "Order cancelled by customer")
    db.commit()
    return get_order_or_404(db, order.id)


@router.post(
    "/{order_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
def review_order(
    order_id: int,
    payload: ReviewIn,
    db: Session = Depends(get_db),
    customer: User = Depends(customer_only),
):
    order = get_order_or_404(db, order_id, customer_id=customer.id)
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You can only review an order after it is delivered"
        )
    if order.review is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This order has already been reviewed")

    review = Review(
        order_id=order.id,
        customer_id=customer.id,
        restaurant_id=order.restaurant_id,
        rating=payload.rating,
        comment=(payload.comment or "").strip() or None,
    )
    db.add(review)
    db.commit()
    return review


@router.post(
    "/{order_id}/return", response_model=ReturnOut, status_code=status.HTTP_201_CREATED
)
def request_return(
    order_id: int,
    payload: ReturnIn,
    db: Session = Depends(get_db),
    customer: User = Depends(customer_only),
):
    order = get_order_or_404(db, order_id, customer_id=customer.id)
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A return/refund can only be requested after the order is delivered",
        )
    if order.return_request is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A return has already been requested for this order"
        )

    request = ReturnRequest(
        order_id=order.id, reason=payload.reason, status=ReturnStatus.REQUESTED
    )
    db.add(request)
    order.return_status = ReturnStatus.REQUESTED
    db.commit()
    return request
