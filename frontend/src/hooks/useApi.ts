"use client";

import { useCallback, useEffect, useState } from "react";

interface ApiState<T> {
  data: T | undefined;
  error: string | undefined;
  loading: boolean;
}

/**
 * Runs `load` on mount and whenever its identity changes (memoize it with
 * useCallback). `reload()` re-runs it while keeping the current data on screen.
 */
export function useApi<T>(load: () => Promise<T>) {
  const [state, setState] = useState<ApiState<T>>({
    data: undefined,
    error: undefined,
    loading: true,
  });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    load().then(
      (data) => {
        if (!cancelled) setState({ data, error: undefined, loading: false });
      },
      (err: unknown) => {
        if (!cancelled) {
          setState((s) => ({
            ...s,
            error: err instanceof Error ? err.message : "Request failed",
            loading: false,
          }));
        }
      },
    );
    return () => {
      cancelled = true;
    };
  }, [load, version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);

  return { ...state, reload };
}
