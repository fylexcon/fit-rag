"use client";

import type { TooltipContentProps } from "recharts";

export const AXIS_TICK = { fill: "var(--chart-axis)", fontSize: 11 };
export const GRID_STROKE = "var(--chart-grid)";

interface ChartTooltipProps extends Partial<TooltipContentProps<number, string>> {
  /** Formats the hovered x value (category or number) for the tooltip heading. */
  formatLabel?: (label: string | number) => string;
  valueFormatter: (value: number) => string;
  seriesLabel: string;
  color: string;
}

/** Tooltip card: values in text ink, the colored swatch carries series identity. */
export function ChartTooltip({
  active,
  payload,
  label,
  formatLabel,
  valueFormatter,
  seriesLabel,
  color,
}: ChartTooltipProps) {
  const value = payload?.[0]?.value;
  if (!active || value == null || label == null) return null;
  return (
    <div className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-md dark:border-zinc-700 dark:bg-zinc-900">
      <p className="mb-1 text-zinc-500">{formatLabel ? formatLabel(label) : label}</p>
      <p className="flex items-center gap-2 font-medium text-zinc-900 dark:text-zinc-100">
        <span className="h-2 w-2 rounded-full" style={{ background: color }} />
        {seriesLabel}: {valueFormatter(Number(value))}
      </p>
    </div>
  );
}
