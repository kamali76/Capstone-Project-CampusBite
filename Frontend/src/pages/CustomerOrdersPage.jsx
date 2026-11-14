import { useState } from "react";
import { useLocation } from "react-router-dom";
import useFetch from "../hooks/useFetch";
import { cancelOrder, listMyOrders, requestReturn, reviewOrder } from "../api/orders";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import OrderSummary from "../components/OrderSummary";
import Pagination from "../components/Pagination";
import ReviewForm from "../components/ReviewForm";
import ReturnForm from "../components/ReturnForm";
import { ALL_STATUSES, ORDER_STATUS } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";
import { prettyStatus } from "../utils/format";

export default function CustomerOrdersPage() {
  const location = useLocation();
  const placedOrderId = location.state?.placedOrderId;

  const [filters, setFilters] = useState({ status: "", dateFrom: "", dateTo: "" });
  const [page, setPage] = useState(1);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(
    placedOrderId ? `Order #${placedOrderId} placed! Payment status: mock_paid.` : ""
  );

  const { data, loading, error: loadError, refetch } = useFetch(
    () => listMyOrders({ ...filters, page }),
    [filters.status, filters.dateFrom, filters.dateTo, page]
  );

  const changeFilter = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
    setPage(1); // a new filter always starts from the first page
  };

  const clearFilters = () => {
    setFilters({ status: "", dateFrom: "", dateTo: "" });
    setPage(1);
  };

  // Runs an API action for one order, then reloads the list
  const runAction = async (orderId, action, successText) => {
    setError("");
    setSuccess("");
    setBusyId(orderId);
    try {
      await action();
      setSuccess(successText);
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleCancel = (order) => {
    if (!window.confirm(`Cancel order #${order.id}? Your payment will be refunded.`)) return;
    runAction(order.id, () => cancelOrder(order.id), `Order #${order.id} cancelled and refunded.`);
  };

  const orders = data?.items || [];

  return (
    <div>
      <h2>My orders</h2>
      <SuccessMessage message={success} />
      <ErrorMessage message={error || loadError} />

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
      </div>

      {loading && !data && <Loader text="Loading your orders..." />}
      {loading && data && <Loader text="Updating..." />}

      {!loading && !loadError && orders.length === 0 && <p>No orders found.</p>}

      <div className="order-list">
        {orders.map((order) => {
          const busy = busyId === order.id;
          const delivered = order.status === ORDER_STATUS.DELIVERED;
          return (
            <OrderSummary key={order.id} order={order} perspective="customer" showTracker>
              {order.status === ORDER_STATUS.PLACED && (
                <button type="button" className="danger" disabled={busy} onClick={() => handleCancel(order)}>
                  Cancel order
                </button>
              )}
              {delivered && !order.review && (
                <ReviewForm
                  disabled={busy}
                  onSubmit={(payload) =>
                    runAction(order.id, () => reviewOrder(order.id, payload), "Thanks for your review!")
                  }
                />
              )}
              {delivered && !order.return_request && (
                <ReturnForm
                  disabled={busy}
                  onSubmit={(reason) =>
                    runAction(
                      order.id,
                      () => requestReturn(order.id, reason),
                      "Return request sent to the restaurant."
                    )
                  }
                />
              )}
            </OrderSummary>
          );
        })}
      </div>

      <Pagination page={data?.page || 1} pages={data?.pages} total={data?.total} onChange={setPage} />
    </div>
  );
}
