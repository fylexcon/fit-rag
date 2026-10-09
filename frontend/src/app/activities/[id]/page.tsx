"use client";

import { useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { StreamChart } from "@/components/StreamChart";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { formatDateTime, formatDuration, formatPace, sourceLabel, titleCase } from "@/lib/format";
import type { ActivityDetail } from "@/lib/types";

export default function ActivityDetailPage() {
  return (
    <RequireAuth>
      <AppHeader />
      <main className="mx-auto w-full max-w-4xl flex-1 space-y-6 px-4 py-6">
        <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
          ← Back to dashboard
        </Link>
        <ActivityDetailView />
      </main>
    </RequireAuth>
  );
}

function ActivityDetailView() {
  const { id } = useParams<{ id: string }>();
  const load = useCallback(() => api.getActivity(id), [id]);
  const { data, error, loading } = useApi(load);

  if (loading && !data) {
    return <div className="card h-40 animate-pulse" aria-label="Loading activity" />;
  }
  if (error || !data) {
    return (
      <div className="card text-sm">
        <p className="font-medium">Activity unavailable</p>
        <p className="text-zinc-500">{error ?? "Not found"}</p>
      </div>
    );
  }
  return <ActivityDetailContent detail={data} />;
}

function ActivityDetailContent({ detail }: { detail: ActivityDetail }) {
  const { activity, raw } = detail;
  const streams = raw?.streams ?? [];
  const hrPoints = streams.filter((p) => p.heart_rate != null);
  const pacePoints = streams.filter((p) => p.pace_min_per_km != null);

  const metrics: { label: string; value: string }[] = [
    { label: "Duration", value: formatDuration(activity.duration_minutes) },
  ];
  if (activity.distance_km != null) metrics.push({ label: "Distance", value: `${activity.distance_km.toFixed(2)} km` });
  if (activity.distance_km && activity.duration_minutes) {
    metrics.push({ label: "Avg pace", value: formatPace(activity.duration_minutes / activity.distance_km) });
  }
  if (activity.avg_heart_rate != null) metrics.push({ label: "Avg heart rate", value: `${activity.avg_heart_rate} bpm` });
  if (activity.resting_heart_rate != null) metrics.push({ label: "Resting HR", value: `${activity.resting_heart_rate} bpm` });
  if (activity.steps != null) metrics.push({ label: "Steps", value: activity.steps.toLocaleString() });

  return (
    <>
      <section className="card">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">{sourceLabel(activity.source)}</p>
        <h1 className="mt-1 text-2xl font-semibold">{titleCase(activity.activity_type)}</h1>
        <p className="text-sm text-zinc-500">{formatDateTime(activity.start_time)}</p>

        <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {metrics.map((m) => (
            <div key={m.label} className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
              <dt className="text-xs text-zinc-500">{m.label}</dt>
              <dd className="mt-1 text-lg font-semibold tabular-nums">{m.value}</dd>
            </div>
          ))}
        </dl>

        {activity.notes && <p className="mt-5 text-sm leading-6 text-zinc-700 dark:text-zinc-300">{activity.notes}</p>}
      </section>

      {hrPoints.length > 1 && (
        <StreamChart
          title="Heart rate"
          unit="bpm"
          points={hrPoints}
          dataKey="heart_rate"
          color="var(--series-1)"
          valueFormatter={(v) => `${Math.round(v)} bpm`}
        />
      )}
      {pacePoints.length > 1 && (
        <StreamChart
          title="Pace"
          unit="min/km"
          points={pacePoints}
          dataKey="pace_min_per_km"
          color="var(--series-2)"
          valueFormatter={formatPace}
          reversed
        />
      )}
      {hrPoints.length <= 1 && pacePoints.length <= 1 && (
        <p className="card text-sm text-zinc-500">
          No per-second stream data was recorded for this activity.
        </p>
      )}

      {raw && (raw.extracted != null || raw.payload != null) && (
        <details className="card text-sm">
          <summary className="cursor-pointer font-medium">Raw data</summary>
          <p className="mt-2 text-xs text-zinc-500">
            Stored in MongoDB ({raw.id}){raw.has_image ? " · original screenshot not shown" : ""}
          </p>
          <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-zinc-50 p-3 font-mono text-xs dark:bg-zinc-950">
            {JSON.stringify(raw.extracted ?? raw.payload, null, 2)}
          </pre>
        </details>
      )}
    </>
  );
}
