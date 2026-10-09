"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AXIS_TICK, ChartTooltip, GRID_STROKE } from "@/components/charts/chartTheme";
import type { StreamPoint } from "@/lib/types";

interface Props {
  title: string;
  unit: string;
  points: StreamPoint[];
  dataKey: "heart_rate" | "pace_min_per_km";
  color: string;
  valueFormatter: (v: number) => string;
  /** Lower is better (pace): flip the axis so "up" still reads as "better". */
  reversed?: boolean;
}

function formatElapsed(sec: number | string): string {
  const s = Math.round(Number(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function StreamChart({ title, unit, points, dataKey, color, valueFormatter, reversed }: Props) {
  return (
    <figure className="card">
      <figcaption className="mb-3 text-sm">
        <span className="font-medium">{title}</span> <span className="text-zinc-500">· {unit}</span>
      </figcaption>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid vertical={false} stroke={GRID_STROKE} />
            <XAxis
              dataKey="elapsed_sec"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickFormatter={formatElapsed}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
              minTickGap={24}
            />
            <YAxis
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={false}
              reversed={reversed}
              domain={["auto", "auto"]}
              tickFormatter={(v: number) => valueFormatter(v).split(" ")[0]}
            />
            <Tooltip
              cursor={{ stroke: "var(--chart-axis)", strokeDasharray: "3 3" }}
              content={<ChartTooltip seriesLabel={title} color={color} formatLabel={(l) => `${formatElapsed(l)} elapsed`} valueFormatter={valueFormatter} />}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, stroke: "var(--chart-surface)", strokeWidth: 2 }}
              connectNulls
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
