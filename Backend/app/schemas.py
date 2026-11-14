"""Pydantic request/response schemas."""
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, field_validator

# Timestamps are stored as naive UTC; serialise them with a trailing "Z" so that
# browsers (new Date(...)) interpret them as UTC instead of local time.
UTCDateTime = Annotated[
    datetime,
    PlainSerializer(
        lambda d: d.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        return_type=str,
    ),
]

RoleLiteral = Literal["CUSTOMER", "RESTAURANT_OWNER", "DELIVERY_PARTNER"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    role: RoleLiteral = "CUSTOMER"
    phone: Optional[str] = Field(default=None, max_length=20)
    restaurant_name: Optional[str] = Field(default=None, max_length=120)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long")
        return value

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(ORMModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str


class UserMini(ORMModel):
    id: int
    name: str
    phone: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Restaurants & menu ----------
class RestaurantOut(BaseModel):
    id: int
    name: str
    cuisine: str
    description: str
    address: str
    rating: Optional[float] = None
    review_count: int = 0


class RestaurantUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    cuisine: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=500)
    address: str = Field(default="", max_length=255)


class RestaurantMini(ORMModel):
    id: int
    name: str


class MenuItemOut(ORMModel):
    id: int
    restaurant_id: int
    category: str
    name: str
    description: str
    price: float
    is_available: bool


class MenuItemIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    category: str = Field(default="General", min_length=1, max_length=50)
    price: float = Field(gt=0, le=100000)
    is_available: bool = True


class AvailabilityIn(BaseModel):
    is_available: bool


# ---------- Orders ----------
class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, le=50)


class OrderCreate(BaseModel):
    restaurant_id: int
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    delivery_address: str = Field(min_length=5, max_length=500)


class OrderItemOut(ORMModel):
    id: int
    menu_item_id: Optional[int] = None
    name: str
    unit_price: float
    quantity: int


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewOut(ORMModel):
    id: int
    rating: int
    comment: Optional[str] = None
    created_at: UTCDateTime


class ReturnIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("Please give a reason of at least 5 characters")
        return value


class ReturnOut(ORMModel):
    id: int
    order_id: int
    reason: str
    status: str
    created_at: UTCDateTime
    decided_at: Optional[UTCDateTime] = None


class PaymentOut(ORMModel):
    id: int
    entry_type: str
    amount: float
    status: str
    reference: str
    note: Optional[str] = None
    created_at: UTCDateTime


class OrderOut(ORMModel):
    id: int
    status: str
    total_amount: float
    delivery_address: str
    payment_status: str
    return_status: str
    created_at: UTCDateTime
    updated_at: UTCDateTime
    restaurant: RestaurantMini
    customer: UserMini
    delivery_partner: Optional[UserMini] = None
    items: list[OrderItemOut]
    payments: list[PaymentOut] = []
    review: Optional[ReviewOut] = None
    return_request: Optional[ReturnOut] = None


class Page(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class OrderPage(Page):
    items: list[OrderOut]


class OwnerStatusIn(BaseModel):
    status: str


class DeliveryStatusIn(BaseModel):
    status: str


class AssignIn(BaseModel):
    delivery_partner_id: int


# ---------- Returns (owner view) ----------
class ReturnDecisionIn(BaseModel):
    decision: Literal["approve", "reject"]


class OwnerReturnOut(ReturnOut):
    order: OrderOut


class OwnerReturnPage(Page):
    items: list[OwnerReturnOut]


# ---------- Owner extras ----------
class ReminderOut(BaseModel):
    id: int
    order_id: int
    status_at_time: str
    message: str
    created_at: UTCDateTime
    still_pending: bool


class TopItem(BaseModel):
    name: str
    quantity: int


class StatsOut(BaseModel):
    total_orders: int
    orders_today: int
    revenue: float
    average_order_value: float
    orders_by_status: dict[str, int]
    top_items: list[TopItem]
    average_rating: Optional[float] = None
    review_count: int
    pending_returns: int
    active_reminders: int


# ---------- AI ----------
class AIQuery(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    # Client's minutes ahead of UTC (IST = 330), so "this week" / "today" mean local time
    tz_offset: int = Field(default=0, ge=-840, le=840)


class AIAnswer(BaseModel):
    answer: str
    orders_considered: int
