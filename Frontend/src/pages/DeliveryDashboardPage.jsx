import { useState } from "react";
import useFetch from "../hooks/useFetch";
import { listDeliveries, listDeliveryHistory, setDeliveryStatus } from "../api/delivery";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import OrderSummary from "../components/OrderSummary";
import Pagination from "../components/Pagination";
import { ORDER_STATUS } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";
import { prettyStatus } from "../utils/format";

const TABS = { ACTIVE: "active", HISTORY: "history" };

export default function DeliveryDashboardPage() {
  const [tab, setTab] = useState(TABS.ACTIVE);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { data, loading, error: loadError, refetch } = useFetch(
    () =>
      tab === TABS.ACTIVE
        ? listDeliveries({ status: statusFilter, page })
        : listDeliveryHistory({ page }),
    [tab, statusFilter, page]
  );

  const switchTab = (next) => {
    setTab(next);
    setPage(1);
    setStatusFilter("");
    setError("");
    setSuccess("");
  };

  const changeStatusFilter = (value) => {
    setStatusFilter(value);
    setPage(1);
  };

  const updateStatus = async (order, status) => {
    setError("");
    setSuccess("");
    setBusyId(order.id);
    try {
      await setDeliveryStatus(order.id, status);
      setSuccess(`Order #${order.id} marked as ${prettyStatus(status)}.`);
      refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const orders = data?.items || [];

  return (
    <div>
      <h2>Delivery dashboard</h2>

      <div className="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === TABS.ACTIVE}
          className={`tab ${tab === TABS.ACTIVE ? "active" : ""}`}
          onClick={() => switchTab(TABS.ACTIVE)}
        >
          Assigned deliveries
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === TABS.HISTORY}
          className={`tab ${tab === TABS.HISTORY ? "active" : ""}`}
          onClick={() => switchTab(TABS.HISTORY)}
        >
          Delivery history
        </button>
      </div>

      <SuccessMessage message={success} />
      <ErrorMessage message={error || loadError} />

      {tab === TABS.ACTIVE && (
        <div className="filters">
          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(e) => changeStatusFilter(e.target.value)}
          >
            <option value="">All active deliveries</option>
            <option value={ORDER_STATUS.ASSIGNED}>{prettyStatus(ORDER_STATUS.ASSIGNED)}</option>
            <option value={ORDER_STATUS.OUT_FOR_DELIVERY}>{prettyStatus(ORDER_STATUS.OUT_FOR_DELIVERY)}</option>
          </select>
          <button type="button" className="secondary" onClick={refetch}>
            Refresh
          </button>
        </div>
      )}

      {loading && !data && <Loader text="Loading deliveries..." />}
      {loading && data && <Loader text="Updating..." />}
      {!loading && !loadError && orders.length === 0 && (
        <p>{tab === TABS.ACTIVE ? "No active deliveries right now." : "No completed deliveries yet."}</p>
      )}

      <div className="order-list">
        {orders.map((order) => (
          <OrderSummary key={order.id} order={order} perspective="delivery">
            {tab === TABS.ACTIVE && order.status === ORDER_STATUS.ASSIGNED && (
              <button
                type="button"
                disabled={busyId === order.id}
                onClick={() => updateStatus(order, ORDER_STATUS.OUT_FOR_DELIVERY)}
              >
                Pick up · Out for delivery
              </button>
            )}
            {tab === TABS.ACTIVE && order.status === ORDER_STATUS.OUT_FOR_DELIVERY && (
              <button
                type="button"
                disabled={busyId === order.id}
                onClick={() => updateStatus(order, ORDER_STATUS.DELIVERED)}
              >
                Mark as delivered
              </button>
            )}
          </OrderSummary>
        ))}
      </div>

      <Pagination page={data?.page || 1} pages={data?.pages} total={data?.total} onChange={setPage} />
    </div>
  );
}
