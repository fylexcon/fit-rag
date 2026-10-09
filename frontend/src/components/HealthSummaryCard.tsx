"use client";

import { useCallback, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AXIS_TICK, ChartTooltip, GRID_STROKE } from "@/components/charts/chartTheme";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { formatDay } from "@/lib/format";
import type { DailyHealthMetric } from "@/lib/types";

const RANGES = [7, 14, 30] as const;

export function HealthSummaryCard() {
  const [days, setDays] = useState<(typeof RANGES)[number]>(7);
  const load = useCallback(() => api.getHealthSummary(days), [days]);
  const { data, error, loading } = useApi(load);

  const daily = data?.daily ?? [];
  const hasSleep = daily.some((d) => d.sleep_hours != null);
  const hasRhr = daily.some((d) => d.resting_heart_rate != null);

  return (
    <section className="card">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Health trends</h2>
        <div role="group" aria-label="Time range" className="flex rounded-md border border-zinc-200 text-xs dark:border-zinc-700">
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              aria-pressed={days === r}
              onClick={() => setDays(r)}
              className={`px-2.5 py-1 font-medium first:rounded-l-md last:rounded-r-md ${
                days === r ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900" : "text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
              }`}
            >
              {r}d
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600">Couldn&apos;t load health data: {error}</p>}

      <dl className="grid grid-cols-3 gap-3">
        <StatTile label="Avg sleep" value={data?.avg_sleep_hours != null ? `${data.avg_sleep_hours.toFixed(1)} h` : "—"} loading={loading && !data} />
        <StatTile label="Resting HR" value={data?.avg_resting_heart_rate != null ? `${Math.round(data.avg_resting_heart_rate)} bpm` : "—"} loading={loading && !data} />
        <StatTile label="Steps" value={data?.total_steps != null ? data.total_steps.toLocaleString() : "—"} loading={loading && !data} />
      </dl>

      {data && (
        <div className="mt-6 space-y-6">
          <ChartBlock title="Sleep" unit="hours per night" empty={!hasSleep}>
            <BarChart data={daily} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <CartesianGrid vertical={false} stroke={GRID_STROKE} />
              <XAxis dataKey="date" tickFormatter={formatDay} tick={AXIS_TICK} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={12} />
              <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip
                cursor={{ fill: GRID_STROKE, opacity: 0.5 }}
                content={<ChartTooltip seriesLabel="Sleep" color="var(--series-1)" formatLabel={(l) => formatDay(String(l))} valueFormatter={(v) => `${v.toFixed(1)} h`} />}
              />
              <Bar dataKey="sleep_hours" fill="var(--series-1)" radius={[4, 4, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ChartBlock>

          <ChartBlock title="Resting heart rate" unit="bpm" empty={!hasRhr}>
            <LineChart data={daily} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
              <CartesianGrid vertical={false} stroke={GRID_STROKE} />
              <XAxis dataKey="date" tickFormatter={formatDay} tick={AXIS_TICK} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={12} />
              <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} domain={["dataMin - 3", "dataMax + 3"]} allowDecimals={false} />
              <Tooltip
                cursor={{ stroke: "var(--chart-axis)", strokeDasharray: "3 3" }}
                content={<ChartTooltip seriesLabel="Resting HR" color="var(--series-1)" formatLabel={(l) => formatDay(String(l))} valueFormatter={(v) => `${Math.round(v)} bpm`} />}
              />
              <Line
                type="monotone"
                dataKey="resting_heart_rate"
                stroke="var(--series-1)"
                strokeWidth={2}
                dot={{ r: 4, fill: "var(--series-1)", stroke: "var(--chart-surface)", strokeWidth: 2 }}
                activeDot={{ r: 5, stroke: "var(--chart-surface)", strokeWidth: 2 }}
              />
            </LineChart>
          </ChartBlock>

          <DataTable daily={daily} />
        </div>
      )}
    </section>
  );
}

function StatTile({ label, value, loading }: { label: string; value: string; loading: boolean }) {
  return (
    <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="mt-1 text-lg font-semibold tabular-nums">
        {loading ? <span className="inline-block h-5 w-12 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" /> : value}
      </dd>
    </div>
  );
}

function ChartBlock({ title, unit, empty, children }: { title: string; unit: string; empty: boolean; children: React.ReactElement }) {
  return (
    <figure>
      <figcaption className="mb-2 text-sm">
        <span className="font-medium">{title}</span> <span className="text-zinc-500">· {unit}</span>
      </figcaption>
      {empty ? (
        <p className="flex h-32 items-center justify-center rounded-lg border border-dashed border-zinc-200 text-xs text-zinc-500 dark:border-zinc-700">
          No data in this range yet
        </p>
      ) : (
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            {children}
          </ResponsiveContainer>
        </div>
      )}
    </figure>
  );
}

function DataTable({ daily }: { daily: DailyHealthMetric[] }) {
  return (
    <details className="text-sm">
      <summary className="cursor-pointer text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200">Show as table</summary>
      <table className="mt-2 w-full text-left text-xs tabular-nums">
        <thead className="text-zinc-500">
          <tr>
            <th className="py-1 font-medium">Day</th>
            <th className="py-1 text-right font-medium">Sleep (h)</th>
            <th className="py-1 text-right font-medium">Resting HR</th>
            <th className="py-1 text-right font-medium">Steps</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {daily.map((d) => (
            <tr key={d.date}>
              <td className="py-1">{formatDay(d.date)}</td>
              <td className="py-1 text-right">{d.sleep_hours?.toFixed(1) ?? "—"}</td>
              <td className="py-1 text-right">{d.resting_heart_rate != null ? Math.round(d.resting_heart_rate) : "—"}</td>
              <td className="py-1 text-right">{d.steps?.toLocaleString() ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
