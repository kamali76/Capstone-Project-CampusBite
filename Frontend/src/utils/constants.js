export const ROLES = {
  CUSTOMER: "CUSTOMER",
  OWNER: "RESTAURANT_OWNER",
  DELIVERY: "DELIVERY_PARTNER",
};

export const ORDER_STATUS = {
  PLACED: "PLACED",
  ACCEPTED: "ACCEPTED",
  PREPARING: "PREPARING",
  READY: "READY",
  ASSIGNED: "ASSIGNED",
  OUT_FOR_DELIVERY: "OUT_FOR_DELIVERY",
  DELIVERED: "DELIVERED",
  CANCELLED: "CANCELLED",
  REFUNDED: "REFUNDED",
};

// Happy-path order of the lifecycle, used by the status tracker
export const ORDER_FLOW = [
  ORDER_STATUS.PLACED,
  ORDER_STATUS.ACCEPTED,
  ORDER_STATUS.PREPARING,
  ORDER_STATUS.READY,
  ORDER_STATUS.ASSIGNED,
  ORDER_STATUS.OUT_FOR_DELIVERY,
  ORDER_STATUS.DELIVERED,
];

export const ALL_STATUSES = Object.values(ORDER_STATUS);

export const TOKEN_KEY = "campusbite_token";
export const USER_KEY = "campusbite_user";
export const CART_KEY_PREFIX = "campusbite_cart_";
