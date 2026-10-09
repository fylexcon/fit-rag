import Link from "next/link";
import type { Activity } from "@/lib/types";
import { formatDateTime, formatDuration, sourceLabel, titleCase } from "@/lib/format";

interface Props {
  activities: Activity[] | undefined;
  total: number;
  loading: boolean;
  error: string | undefined;
  onLoadMore: () => void;
}

export function ActivityFeed({ activities, total, loading, error, onLoadMore }: Props) {
  return (
    <section className="card">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Activity feed</h2>
        {activities && <span className="text-xs text-zinc-500">{total} total</span>}
      </div>

      {error && <p className="text-sm text-red-600">Couldn&apos;t load activities: {error}</p>}

      {loading && !activities && <FeedSkeleton />}

      {activities && activities.length === 0 && (
        <p className="py-8 text-center text-sm text-zinc-500">
          No activities yet. Log a workout or connect Huawei Health to get started.
        </p>
      )}

      {activities && activities.length > 0 && (
        <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {activities.map((a) => (
            <li key={a.id}>
              <Link
                href={`/activities/${a.id}`}
                className="-mx-2 flex items-center justify-between gap-4 rounded-md px-2 py-3 transition hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{titleCase(a.activity_type)}</p>
                  <p className="text-xs text-zinc-500">
                    {formatDateTime(a.start_time)} · {sourceLabel(a.source)}
                  </p>
                </div>
                <div className="flex shrink-0 gap-4 text-right text-sm tabular-nums">
                  {a.distance_km != null && <Metric label="km" value={a.distance_km.toFixed(1)} />}
                  {a.avg_heart_rate != null && <Metric label="bpm" value={String(a.avg_heart_rate)} />}
                  <Metric label="time" value={formatDuration(a.duration_minutes)} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {activities && activities.length < total && (
        <button type="button" onClick={onLoadMore} className="btn-secondary mt-4 w-full">
          Load more
        </button>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-medium">{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
    </div>
  );
}

function FeedSkeleton() {
  return (
    <ul className="space-y-3" aria-label="Loading activities">
      {[0, 1, 2].map((i) => (
        <li key={i} className="h-12 animate-pulse rounded-md bg-zinc-100 dark:bg-zinc-800" />
      ))}
    </ul>
  );
}
