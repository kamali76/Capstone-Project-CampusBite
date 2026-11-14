import client from "./client";
import { cleanParams } from "../utils/format";

export const listDeliveries = ({ status = "", page = 1, pageSize = 6 } = {}) =>
  client.get("/delivery/orders", { params: cleanParams({ status, page, page_size: pageSize }) });

export const listDeliveryHistory = ({ page = 1, pageSize = 6 } = {}) =>
  client.get("/delivery/history", { params: { page, page_size: pageSize } });

export const setDeliveryStatus = (id, status) =>
  client.patch(`/delivery/orders/${id}/status`, { status });
