import StatusBadge from "./StatusBadge";
import OrderStatusTracker from "./OrderStatusTracker";
import { formatDateTime, formatPrice, prettyStatus } from "../utils/format";

/**
 * One order card, shared by all three dashboards.
 * `perspective` decides who is shown as the "other party":
 *   customer -> restaurant + delivery partner
 *   owner / delivery -> customer name, phone and address
 * Action buttons/forms are passed in as `children`.
 */
export default function OrderSummary({ order, perspective = "customer", showTracker = false, children }) {
  const title =
    perspective === "customer" ? order.restaurant.name : order.customer.name;

  return (
    <article className="card order-card">
      <header className="order-header">
        <div>
          <h3>
            Order #{order.id} · {title}
          </h3>
          <p className="muted">{formatDateTime(order.created_at)}</p>
        </div>
        <StatusBadge status={order.status} />
      </header>

      {showTracker && <OrderStatusTracker status={order.status} />}

      <ul className="order-items">
        {order.items.map((item) => (
          <li key={item.id}>
            <span>
              {item.quantity} × {item.name}
            </span>
            <span>{formatPrice(item.unit_price * item.quantity)}</span>
          </li>
        ))}
      </ul>

      <p className="order-total">
        <strong>Total: {formatPrice(order.total_amount)}</strong>
      </p>

      <div className="order-meta">
        <p>
          <span className="muted">Payment:</span>{" "}
          <span className={`pill pill-${order.payment_status}`}>{prettyStatus(order.payment_status)}</span>
        </p>
        {order.return_status !== "none" && (
          <p>
            <span className="muted">Return/refund:</span>{" "}
            <span className={`pill pill-${order.return_status}`}>{prettyStatus(order.return_status)}</span>
          </p>
        )}
        <p>
          <span className="muted">Deliver to:</span> {order.delivery_address}
        </p>
        {perspective !== "customer" && order.customer.phone && (
          <p>
            <span className="muted">Customer phone:</span> {order.customer.phone}
          </p>
        )}
        {perspective !== "delivery" && order.delivery_partner && (
          <p>
            <span className="muted">Delivery partner:</span> {order.delivery_partner.name}
          </p>
        )}
        {order.review && (
          <p>
            <span className="muted">Review:</span> {"⭐".repeat(order.review.rating)}
            {order.review.comment ? ` — ${order.review.comment}` : ""}
          </p>
        )}
        {order.return_request && (
          <p>
            <span className="muted">Return reason:</span> {order.return_request.reason}
          </p>
        )}
      </div>

      {order.payments?.length > 0 && (
        <details className="payment-log">
          <summary>Payment records ({order.payments.length})</summary>
          <ul>
            {order.payments.map((p) => (
              <li key={p.id}>
                {prettyStatus(p.entry_type)} · {formatPrice(p.amount)} · {p.reference}
                <span className="muted"> · {formatDateTime(p.created_at)}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {children && <div className="order-actions">{children}</div>}
    </article>
  );
}
