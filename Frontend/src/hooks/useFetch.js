import { useCallback, useEffect, useState } from "react";
import { getErrorMessage } from "../utils/errors";

/**
 * Loads data with loading + error state.
 *
 *   const { data, loading, error, refetch } = useFetch(() => getRestaurants(), []);
 *
 * `deps` works like useEffect deps: the request re-runs when any of them change.
 * `data` keeps the last successful result while a new request is in flight,
 * so lists don't blank out on every filter change or refetch.
 */
export default function useFetch(fetcher, deps = []) {
  const [reloadKey, setReloadKey] = useState(0);
  const [result, setResult] = useState({ key: null, data: null, error: "" });

  // Identifies "this particular request"; loading = the stored result is for an older key
  const key = `${JSON.stringify(deps)}|${reloadKey}`;

  useEffect(() => {
    let cancelled = false; // ignore answers from outdated requests
    fetcher()
      .then((res) => {
        if (!cancelled) setResult({ key, data: res.data, error: "" });
      })
      .catch((err) => {
        if (!cancelled) setResult((prev) => ({ key, data: prev.data, error: getErrorMessage(err) }));
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const refetch = useCallback(() => setReloadKey((k) => k + 1), []);
  const loading = result.key !== key;

  return { data: result.data, loading, error: loading ? "" : result.error, refetch };
}
