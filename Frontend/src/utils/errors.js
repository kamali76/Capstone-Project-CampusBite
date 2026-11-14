// Turns an axios error into a readable message.
// FastAPI sends { detail: "text" } or, for validation errors, { detail: [{ msg, loc }, ...] }.
export function getErrorMessage(err) {
  if (err?.response) {
    const detail = err.response.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => {
          const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
          return field && field !== "body" ? `${field}: ${d.msg}` : d.msg;
        })
        .join(", ");
    }
    return `Request failed (${err.response.status})`;
  }
  if (err?.code === "ERR_NETWORK" || err?.request) {
    return "Cannot reach the server. Please check that the backend is running.";
  }
  return err?.message || "Something went wrong";
}
