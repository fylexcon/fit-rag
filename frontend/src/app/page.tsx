"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityFeed } from "@/components/ActivityFeed";
import { AppHeader } from "@/components/AppHeader";
import { HuaweiConnectCard } from "@/components/HuaweiConnectCard";
import { LogWorkoutModal } from "@/components/LogWorkoutModal";
import { RequireAuth } from "@/components/RequireAuth";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";

const PAGE_SIZE = 20;
// Extraction runs in a Celery worker, so re-poll the feed a few times after a submit.
const REFRESH_AFTER_SUBMIT_MS = [3000, 8000, 15000];

export default function DashboardPage() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}

function Dashboard() {
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [logOpen, setLogOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const timers = useRef<number[]>([]);

  const loadActivities = useCallback(() => api.listActivities(limit), [limit]);
  const activities = useApi(loadActivities);
  const { reload: reloadActivities } = activities;

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const onWorkoutSubmitted = useCallback(() => {
    setNotice("Workout received — extracting details…");
    timers.current.forEach(clearTimeout);
    timers.current = REFRESH_AFTER_SUBMIT_MS.map((ms, i) =>
      window.setTimeout(() => {
        reloadActivities();
        if (i === REFRESH_AFTER_SUBMIT_MS.length - 1) setNotice(null);
      }, ms),
    );
  }, [reloadActivities]);

  return (
    <>
      <AppHeader>
        <button type="button" onClick={() => setLogOpen(true)} className="btn-primary">
          + Log workout
        </button>
      </AppHeader>

      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 py-6">
        {notice && (
          <p role="status" className="rounded-md bg-emerald-50 px-4 py-2 text-sm text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
            {notice}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <ActivityFeed
              activities={activities.data?.items}
              total={activities.data?.total ?? 0}
              loading={activities.loading}
              error={activities.error}
              onLoadMore={() => setLimit((l) => l + PAGE_SIZE)}
            />
          </div>
          <aside className="space-y-6">
            <HuaweiConnectCard />
          </aside>
        </div>
      </main>

      <LogWorkoutModal open={logOpen} onClose={() => setLogOpen(false)} onSubmitted={onWorkoutSubmitted} />
    </>
  );
}
