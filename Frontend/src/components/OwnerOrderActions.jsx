import { useState } from "react";
import { ORDER_STATUS } from "../utils/constants";

// The next step the restaurant can take for an order in a given status
const NEXT_STEP = {
  [ORDER_STATUS.PLACED]: { status: ORDER_STATUS.ACCEPTED, label: "Accept order" },
  [ORDER_STATUS.ACCEPTED]: { status: ORDER_STATUS.PREPARING, label: "Start preparing" },
  [ORDER_STATUS.PREPARING]: { status: ORDER_STATUS.READY, label: "Mark ready" },
};

export default function OwnerOrderActions({ order, partners, busy, onStatus, onAssign }) {
  const [partnerId, setPartnerId] = useState("");
  const next = NEXT_STEP[order.status];

  if (next) {
    return (
      <button type="button" disabled={busy} onClick={() => onStatus(order.id, next.status)}>
        {next.label}
      </button>
    );
  }

  if (order.status === ORDER_STATUS.READY) {
    return (
      <div className="inline-form-row">
        <select value={partnerId} onChange={(e) => setPartnerId(e.target.value)} aria-label="Delivery partner">
          <option value="">Select delivery partner…</option>
          {partners.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button type="button" disabled={busy || !partnerId} onClick={() => onAssign(order.id, Number(partnerId))}>
          Assign
        </button>
      </div>
    );
  }

  return null;
}
