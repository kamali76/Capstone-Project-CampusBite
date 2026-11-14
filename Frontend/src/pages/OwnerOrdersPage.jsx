import { useState } from "react";
import useFetch from "../hooks/useFetch";
import { assignPartner, listOwnerOrders, listPartners, setOrderStatus } from "../api/owner";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import OrderSummary from "../components/OrderSummary";
import OwnerOrderActions from "../components/OwnerOrderActions";
import Pagination from "../components/Pagination";
import { ALL_STATUSES } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";
import { prettyStatus } from "../utils/format";

export default function OwnerOrdersPage() {
  const [filters, setFilters] = useState({ status: "", dateFrom: "", dateTo: "" });
  const [page, setPage] = useState(1);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const orders = useFetch(
    () => listOwnerOrders({ ...filters, page }),
    [filters.status, filters.dateFrom, filters.dateTo, page]
  );
  const partners = useFetch(listPartners, []);

  const changeFilter = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({ status: "", dateFrom: "", dateTo: "" });
    setPage(1);
  };

  const runAction = async (orderId, action, successText) => {
    setError("");
    setSuccess("");
    setBusyId(orderId);
    try {
      await action();
      setSuccess(successText);
      orders.refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleStatus = (orderId, status) =>
    runAction(orderId, () => setOrderStatus(orderId, status), `Order #${orderId} is now ${prettyStatus(status)}.`);

  const handleAssign = (orderId, partnerId) =>
    runAction(orderId, () => assignPartner(orderId, partnerId), `Delivery partner assigned to order #${orderId}.`);

  const list = orders.data?.items || [];

  return (
    <div>
      <h2>Order management</h2>
      <SuccessMessage message={success} />
      <ErrorMessage message={error || orders.error || partners.error} />

      <div className="filters">
        <select
          aria-label="Filter by status"
          value={filters.status}
          onChange={(e) => changeFilter("status", e.target.value)}
        >
          <option value="">All statuses</option>
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>
              {prettyStatus(s)}
            </option>
          ))}
        </select>
        <label className="filter-date">
          From
          <input
            type="date"
            value={filters.dateFrom}
            max={filters.dateTo || undefined}
            onChange={(e) => changeFilter("dateFrom", e.target.value)}
          />
        </label>
        <label className="filter-date">
          To
          <input
            type="date"
            value={filters.dateTo}
            min={filters.dateFrom || undefined}
            onChange={(e) => changeFilter("dateTo", e.target.value)}
          />
        </label>
        <button type="button" className="secondary" onClick={clearFilters}>
          Clear
        </button>
        <button type="button" className="secondary" onClick={orders.refetch}>
          Refresh
        </button>
      </div>

      {orders.loading && !orders.data && <Loader text="Loading orders..." />}
      {orders.loading && orders.data && <Loader text="Updating..." />}
      {!orders.loading && !orders.error && list.length === 0 && <p>No orders found.</p>}

      <div className="order-list">
        {list.map((order) => (
          <OrderSummary key={order.id} order={order} perspective="owner">
            <OwnerOrderActions
              order={order}
              partners={partners.data || []}
              busy={busyId === order.id}
              onStatus={handleStatus}
              onAssign={handleAssign}
            />
          </OrderSummary>
        ))}
      </div>

      <Pagination
        page={orders.data?.page || 1}
        pages={orders.data?.pages}
        total={orders.data?.total}
        onChange={setPage}
      />
    </div>
  );
}
