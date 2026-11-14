import { useState } from "react";
import { Link } from "react-router-dom";
import useFetch from "../hooks/useFetch";
import { decideReturn, getReminders, getStats, listReturns } from "../api/owner";
import Loader from "../components/Loader";
import ErrorMessage from "../components/ErrorMessage";
import SuccessMessage from "../components/SuccessMessage";
import StatCard from "../components/StatCard";
import OrderSummary from "../components/OrderSummary";
import Pagination from "../components/Pagination";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, formatPrice, prettyStatus } from "../utils/format";

export default function OwnerDashboardPage() {
  const [returnsPage, setReturnsPage] = useState(1);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const stats = useFetch(getStats, []);
  const reminders = useFetch(getReminders, []);
  const returns = useFetch(
    () => listReturns({ status: "requested", page: returnsPage }),
    [returnsPage]
  );

  const handleDecision = async (request, decision) => {
    const verb = decision === "approve" ? "approve (refund)" : "reject";
    if (!window.confirm(`Do you want to ${verb} the return for order #${request.order_id}?`)) return;
    setError("");
    setSuccess("");
    setBusyId(request.id);
    try {
      await decideReturn(request.id, decision);
      setSuccess(
        decision === "approve"
          ? `Return approved: order #${request.order_id} refunded.`
          : `Return rejected for order #${request.order_id}.`
      );
      returns.refetch();
      stats.refetch();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const s = stats.data;

  return (
    <div>
      <h2>Restaurant dashboard</h2>
      <SuccessMessage message={success} />
      <ErrorMessage message={error} />

      {/* ---------- statistics ---------- */}
      <section>
        <h3>Overview</h3>
        <ErrorMessage message={stats.error} />
        {stats.loading && !s && <Loader text="Loading statistics..." />}
        {s && (
          <>
            <div className="grid stats-grid">
              <StatCard label="Total orders" value={s.total_orders} />
              <StatCard label="Orders today" value={s.orders_today} />
              <StatCard label="Revenue" value={formatPrice(s.revenue)} hint="excl. cancelled / refunded" />
              <StatCard label="Avg. order value" value={formatPrice(s.average_order_value)} />
              <StatCard
                label="Rating"
                value={s.average_rating ? `⭐ ${s.average_rating}` : "–"}
                hint={`${s.review_count} review${s.review_count === 1 ? "" : "s"}`}
              />
              <StatCard label="Pending returns" value={s.pending_returns} />
            </div>

            <div className="two-col">
              <div className="card">
                <h4>Orders by status</h4>
                {Object.keys(s.orders_by_status).length === 0 ? (
                  <p className="muted">No orders yet.</p>
                ) : (
                  <ul className="plain-list">
                    {Object.entries(s.orders_by_status).map(([status, count]) => (
                      <li key={status}>
                        <span>{prettyStatus(status)}</span>
                        <strong>{count}</strong>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="card">
                <h4>Most ordered dishes</h4>
                {s.top_items.length === 0 ? (
                  <p className="muted">No data yet.</p>
                ) : (
                  <ol className="plain-list">
                    {s.top_items.map((item) => (
                      <li key={item.name}>
                        <span>{item.name}</span>
                        <strong>{item.quantity}</strong>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            </div>
          </>
        )}
      </section>

      {/* ---------- reminders ---------- */}
      <section>
        <h3>
          Reminders{" "}
          {reminders.data?.length > 0 && <span className="cart-count">{reminders.data.length}</span>}
        </h3>
        <ErrorMessage message={reminders.error} />
        {reminders.loading && !reminders.data && <Loader text="Checking for stale orders..." />}
        {reminders.data?.length === 0 && (
          <p className="muted">All caught up: no orders are waiting for more than 15 minutes.</p>
        )}
        <ul className="reminder-list">
          {reminders.data?.map((r) => (
            <li key={r.id} className="reminder">
              <span>⏰ {r.message}</span>
              <span className="muted">{formatDateTime(r.created_at)}</span>
            </li>
          ))}
        </ul>
        {reminders.data?.length > 0 && <Link to="/owner/orders">Go to orders →</Link>}
      </section>

      {/* ---------- return requests ---------- */}
      <section>
        <h3>Return / refund requests</h3>
        <ErrorMessage message={returns.error} />
        {returns.loading && !returns.data && <Loader text="Loading return requests..." />}
        {returns.data?.items.length === 0 && <p className="muted">No pending return requests.</p>}
        <div className="order-list">
          {returns.data?.items.map((request) => (
            <OrderSummary key={request.id} order={request.order} perspective="owner">
              <p>
                <strong>Customer's reason:</strong> {request.reason}
              </p>
              <div className="inline-form-row">
                <button
                  type="button"
                  disabled={busyId === request.id}
                  onClick={() => handleDecision(request, "approve")}
                >
                  Approve &amp; refund
                </button>
                <button
                  type="button"
                  className="danger"
                  disabled={busyId === request.id}
                  onClick={() => handleDecision(request, "reject")}
                >
                  Reject
                </button>
              </div>
            </OrderSummary>
          ))}
        </div>
        <Pagination
          page={returns.data?.page || 1}
          pages={returns.data?.pages}
          total={returns.data?.total}
          onChange={setReturnsPage}
        />
      </section>
    </div>
  );
}
