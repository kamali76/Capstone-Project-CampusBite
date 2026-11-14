import client from "./client";
import { cleanParams, getTzOffset } from "../utils/format";

// Restaurant profile
export const getMyRestaurant = () => client.get("/owner/restaurant");
export const updateRestaurant = (payload) => client.put("/owner/restaurant", payload);

// Menu
export const listMenuItems = () => client.get("/owner/menu-items");
export const createMenuItem = (payload) => client.post("/owner/menu-items", payload);
export const updateMenuItem = (id, payload) => client.put(`/owner/menu-items/${id}`, payload);
export const setAvailability = (id, isAvailable) =>
  client.patch(`/owner/menu-items/${id}/availability`, { is_available: isAvailable });
export const deleteMenuItem = (id) => client.delete(`/owner/menu-items/${id}`);

// Orders
export const listOwnerOrders = ({ status = "", dateFrom = "", dateTo = "", page = 1, pageSize = 8 }) =>
  client.get("/owner/orders", {
    params: cleanParams({
      status,
      date_from: dateFrom,
      date_to: dateTo,
      tz_offset: getTzOffset(),
      page,
      page_size: pageSize,
    }),
  });
export const setOrderStatus = (id, status) => client.patch(`/owner/orders/${id}/status`, { status });
export const listPartners = () => client.get("/owner/delivery-partners");
export const assignPartner = (id, partnerId) =>
  client.post(`/owner/orders/${id}/assign`, { delivery_partner_id: partnerId });

// Returns / refunds
export const listReturns = ({ status = "", page = 1, pageSize = 5 } = {}) =>
  client.get("/owner/returns", { params: cleanParams({ status, page, page_size: pageSize }) });
export const decideReturn = (id, decision) => client.patch(`/owner/returns/${id}`, { decision });

// Dashboard
export const getStats = () => client.get("/owner/stats", { params: { tz_offset: getTzOffset() } });
export const getReminders = () => client.get("/owner/reminders");
