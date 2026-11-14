export default function Pagination({ page, pages, total, onChange }) {
  if (!pages || pages <= 1) {
    return total ? <p className="muted pagination-total">{total} total</p> : null;
  }
  return (
    <div className="pagination">
      <button type="button" className="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ← Previous
      </button>
      <span>
        Page {page} of {pages}
        {total ? <span className="muted"> · {total} total</span> : null}
      </span>
      <button type="button" className="secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Next →
      </button>
    </div>
  );
}
