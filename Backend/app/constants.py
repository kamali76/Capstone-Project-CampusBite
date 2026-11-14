"""Roles, order statuses and the order state machine."""


class Role:
    CUSTOMER = "CUSTOMER"
    OWNER = "RESTAURANT_OWNER"
    DELIVERY = "DELIVERY_PARTNER"


ALL_ROLES = (Role.CUSTOMER, Role.OWNER, Role.DELIVERY)


class OrderStatus:
    PLACED = "PLACED"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


ALL_STATUSES = (
    OrderStatus.PLACED,
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.ASSIGNED,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED,
    OrderStatus.CANCELLED,
    OrderStatus.REFUNDED,
)

# current status -> {next status: role allowed to perform the move}
TRANSITIONS: dict[str, dict[str, str]] = {
    OrderStatus.PLACED: {
        OrderStatus.ACCEPTED: Role.OWNER,
        OrderStatus.CANCELLED: Role.CUSTOMER,
    },
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING: Role.OWNER},
    OrderStatus.PREPARING: {OrderStatus.READY: Role.OWNER},
    OrderStatus.READY: {OrderStatus.ASSIGNED: Role.OWNER},
    OrderStatus.ASSIGNED: {OrderStatus.OUT_FOR_DELIVERY: Role.DELIVERY},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED: Role.DELIVERY},
    # An approved return request moves a delivered order to REFUNDED
    OrderStatus.DELIVERED: {OrderStatus.REFUNDED: Role.OWNER},
}

# Statuses a restaurant owner may set through the status endpoint.
# ASSIGNED has its own endpoint (needs a delivery partner), REFUNDED goes via returns.
OWNER_SETTABLE = (OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.READY)
DELIVERY_SETTABLE = (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED)

# Orders that are stale-reminder candidates
REMINDER_STATUSES = (OrderStatus.PLACED, OrderStatus.ACCEPTED)

# Orders that no longer count towards revenue
NON_REVENUE_STATUSES = (OrderStatus.CANCELLED, OrderStatus.REFUNDED)


class PaymentStatus:
    MOCK_PAID = "mock_paid"
    REFUNDED = "refunded"


class ReturnStatus:
    NONE = "none"
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
