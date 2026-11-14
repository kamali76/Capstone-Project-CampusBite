import { useState } from "react";

// Rating + comment form shown on delivered orders that have no review yet
export default function ReviewForm({ onSubmit, disabled }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ rating: Number(rating), comment: comment.trim() || null });
  };

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <h4>Rate this order</h4>
      <div className="inline-form-row">
        <label>
          Rating{" "}
          <select value={rating} onChange={(e) => setRating(e.target.value)}>
            {[5, 4, 3, 2, 1].map((n) => (
              <option key={n} value={n}>
                {n} {"⭐".repeat(n)}
              </option>
            ))}
          </select>
        </label>
        <input
          type="text"
          placeholder="Write a short review (optional)"
          maxLength={1000}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        <button type="submit" disabled={disabled}>
          Submit review
        </button>
      </div>
    </form>
  );
}
