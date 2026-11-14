export const formatPrice = (amount) => `₹${Number(amount).toFixed(0)}`;

// The API sends UTC timestamps ending in "Z"; toLocaleString shows them in the user's time zone.
export const formatDateTime = (iso) =>
  iso
    ? new Date(iso).toLocaleString(undefined, {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

// "OUT_FOR_DELIVERY" -> "Out for delivery"
export const prettyStatus = (value) => {
  if (!value) return "";
  const text = String(value).replaceAll("_", " ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

// Minutes ahead of UTC (IST = 330). Sent to the API so date filters mean the user's local days.
export const getTzOffset = () => -new Date().getTimezoneOffset();

// Remove empty values so they are not sent as query params
export const cleanParams = (params) =>
  Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== "" && v !== null && v !== undefined)
  );
