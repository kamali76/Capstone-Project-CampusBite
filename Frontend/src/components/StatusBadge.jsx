import { prettyStatus } from "../utils/format";

export default function StatusBadge({ status }) {
  return <span className={`status-badge status-${String(status).toLowerCase()}`}>{prettyStatus(status)}</span>;
}
