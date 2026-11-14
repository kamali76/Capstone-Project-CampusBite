"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .constants import OrderStatus, PaymentStatus, ReturnStatus
from .database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite does not store time zones)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    restaurant: Mapped[Optional["Restaurant"]] = relationship(
        back_populates="owner", uselist=False
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer", foreign_keys="Order.customer_id"
    )
    deliveries: Mapped[list["Order"]] = relationship(
        back_populates="delivery_partner", foreign_keys="Order.delivery_partner_id"
    )


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    cuisine: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped[User] = relationship(back_populates="restaurant")
    menu_items: Mapped[list["MenuItem"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="restaurant")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    category: Mapped[str] = mapped_column(String(50), default="General")
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_items")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    delivery_partner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default=OrderStatus.PLACED, index=True)
    total_amount: Mapped[float] = mapped_column(Float)
    delivery_address: Mapped[str] = mapped_column(String(500))
    payment_status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.MOCK_PAID)
    return_status: Mapped[str] = mapped_column(String(20), default=ReturnStatus.NONE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    customer: Mapped[User] = relationship(
        back_populates="orders", foreign_keys=[customer_id]
    )
    delivery_partner: Mapped[Optional[User]] = relationship(
        back_populates="deliveries", foreign_keys=[delivery_partner_id]
    )
    restaurant: Mapped[Restaurant] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    review: Mapped[Optional["Review"]] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    return_request: Mapped[Optional["ReturnRequest"]] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    payments: Mapped[list["PaymentLedger"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="PaymentLedger.id"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    menu_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("menu_items.id", ondelete="SET NULL")
    )
    # Snapshot of name/price at order time, so later menu edits don't rewrite history
    name: Mapped[str] = mapped_column(String(100))
    unit_price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique -> at most one review per order
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    order: Mapped[Order] = relationship(back_populates="review")


class PaymentLedger(Base):
    __tablename__ = "payment_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(20))  # payment | refund
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    reference: Mapped[str] = mapped_column(String(60))
    note: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    order: Mapped[Order] = relationship(back_populates="payments")


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique -> a customer cannot raise multiple return requests for one order
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default=ReturnStatus.REQUESTED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    order: Mapped[Order] = relationship(back_populates="return_request")


class AdminReminderLog(Base):
    __tablename__ = "admin_reminder_logs"
    __table_args__ = (
        # One reminder per order per stale status
        UniqueConstraint("order_id", "status_at_time", name="uq_reminder_order_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    status_at_time: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    order: Mapped[Order] = relationship()
