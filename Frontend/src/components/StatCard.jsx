export default function StatCard({ label, value, hint }) {
  return (
    <div className="card stat-card">
      <p className="muted">{label}</p>
      <p className="stat-value">{value}</p>
      {hint && <p className="muted stat-hint">{hint}</p>}
    </div>
  );
}
