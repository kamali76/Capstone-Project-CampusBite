import { useEffect, useState } from "react";

// Returns `value` only after it has stopped changing for `delay` ms,
// so typing in a search box doesn't fire a request on every keystroke.
export default function useDebounce(value, delay = 400) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer); // cleanup cancels the previous timer
  }, [value, delay]);

  return debounced;
}
