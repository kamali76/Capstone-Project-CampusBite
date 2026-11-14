import { ORDER_FLOW, ORDER_STATUS } from "../utils/constants";
import { prettyStatus } from "../utils/format";

// Shows the order's progress through PLACED -> ... -> DELIVERED
export default function OrderStatusTracker({ status }) {
  if (status === ORDER_STATUS.CANCELLED || status === ORDER_STATUS.REFUNDED) {
    return null; // the status badge already says it
  }
  const current = ORDER_FLOW.indexOf(status);
  return (
    <ol className="tracker" aria-label="Order progress">
      {ORDER_FLOW.map((step, index) => {
        const state = index < current ? "done" : index === current ? "current" : "todo";
        return (
          <li key={step} className={`tracker-step ${state}`}>
            <span className="tracker-dot" />
            <span className="tracker-label">{prettyStatus(step)}</span>
          </li>
        );
      })}
    </ol>
  );
}
