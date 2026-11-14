import client from "./client";
import { cleanParams, getTzOffset } from "../utils/format";

export const placeOrder = (payload) => client.post("/orders", payload);

export const listMyOrders = ({ status = "", dateFrom = "", dateTo = "", page = 1, pageSize = 5 }) =>
  client.get("/orders", {
    params: cleanParams({
      status,
      date_from: dateFrom,
      date_to: dateTo,
      tz_offset: getTzOffset(),
      page,
      page_size: pageSize,
    }),
  });

export const cancelOrder = (id) => client.post(`/orders/${id}/cancel`);

export const reviewOrder = (id, payload) => client.post(`/orders/${id}/review`, payload);

export const requestReturn = (id, reason) => client.post(`/orders/${id}/return`, { reason });
