"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function HuaweiConnectCard() {
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function connect() {
    setConnecting(true);
    setError(null);
    try {
      // /auth/huawei/connect needs a Bearer token, which a plain navigation
      // can't carry, so fetch the authorize URL first and then redirect.
      const { url } = await api.getHuaweiAuthorizeUrl();
      window.location.assign(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start Huawei sign-in");
      setConnecting(false);
    }
  }

  return (
    <section className="card">
      <h2 className="text-lg font-semibold">Connected accounts</h2>
      <p className="mt-1 text-sm text-zinc-500">
        Sync sleep, heart rate and workouts automatically every few hours.
      </p>
      <div className="mt-4 flex items-center justify-between gap-4 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-red-600 text-xs font-bold text-white">
            HW
          </span>
          <span className="text-sm font-medium">Huawei Health</span>
        </div>
        <button type="button" onClick={connect} disabled={connecting} className="btn-secondary">
          {connecting ? "Redirecting…" : "Connect Huawei Health"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </section>
  );
}
