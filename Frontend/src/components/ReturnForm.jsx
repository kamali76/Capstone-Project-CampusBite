import { useState } from "react";

// Return/refund request (a reason is mandatory). Collapsed until the customer asks for it.
export default function ReturnForm({ onSubmit, disabled }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(reason.trim());
  };

  if (!open) {
    return (
      <button type="button" className="secondary" onClick={() => setOpen(true)}>
        Request return / refund
      </button>
    );
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <h4>Request a return / refund</h4>
      <div className="inline-form-row">
        <input
          type="text"
          placeholder="Why do you want a refund? (min 5 characters)"
          minLength={5}
          maxLength={500}
          required
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <button type="submit" disabled={disabled || reason.trim().length < 5}>
          Send request
        </button>
        <button type="button" className="secondary" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}
