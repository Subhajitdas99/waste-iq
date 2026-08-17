import { cn } from "@/lib/utils";
import { formatAnalyticsNumber } from "@/lib/analytics";

export interface AnalyticsChartDatum {
  label: string;
  value: number;
  secondaryValue?: number;
  color?: string;
  secondaryColor?: string;
}

interface AnalyticsChartProps {
  data: AnalyticsChartDatum[];
  height?: number;
  primaryColor?: string;
  secondaryColor?: string;
  valueFormatter?: (value: number) => string;
  emptyLabel?: string;
  ariaLabel?: string;
  className?: string;
}

const VIEWBOX_WIDTH = 640;
const DEFAULT_HEIGHT = 240;
const PADDING = { top: 28, right: 8, bottom: 34, left: 8 };
const GRID_LINES = 4;
const LABEL_LIMIT = 8;

export function AnalyticsChart({
  data,
  height = DEFAULT_HEIGHT,
  primaryColor = "#10b981",
  secondaryColor = "#cbd5e1",
  valueFormatter = (value) => formatAnalyticsNumber(value),
  emptyLabel = "No data available for this period.",
  ariaLabel = "Analytics bar chart",
  className,
}: AnalyticsChartProps) {
  const hasData = data.some(
    (datum) => datum.value > 0 || (datum.secondaryValue ?? 0) > 0,
  );

  if (!hasData) {
    return (
      <div className="rounded-2xl border border-dashed bg-muted/20 px-4 py-8 text-center text-sm text-muted-foreground">
        {emptyLabel}
      </div>
    );
  }

  const maxValue = Math.max(
    ...data.map((datum) => Math.max(datum.value, datum.secondaryValue ?? 0)),
  );
  const plotWidth = VIEWBOX_WIDTH - PADDING.left - PADDING.right;
  const plotHeight = height - PADDING.top - PADDING.bottom;
  const groupWidth = plotWidth / data.length;
  const barSlot = Math.min(groupWidth * 0.44, 48);
  const showValueLabels = data.length <= LABEL_LIMIT;

  return (
    <div className={cn("w-full", className)}>
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${height}`}
        className="h-auto w-full"
        role="img"
        aria-label={ariaLabel}
      >
        {Array.from({ length: GRID_LINES + 1 }).map((_, index) => {
          const y = PADDING.top + (plotHeight / GRID_LINES) * index;
          return (
            <line
              key={index}
              x1={PADDING.left}
              x2={VIEWBOX_WIDTH - PADDING.right}
              y1={y}
              y2={y}
              className="stroke-muted/50"
              strokeWidth="1"
            />
          );
        })}

        {data.map((datum, index) => {
          const groupX = PADDING.left + groupWidth * index;
          const groupCenter = groupX + groupWidth / 2;
          const primaryHeight = (datum.value / maxValue) * plotHeight;
          const secondaryHeight =
            (datum.secondaryValue ?? 0) / maxValue * plotHeight;
          const primaryColorValue = datum.color ?? primaryColor;
          const secondaryColorValue =
            datum.secondaryColor ?? secondaryColor;
          const bars = [];
          const formattedValue = valueFormatter(datum.value);
          const formattedSecondary = valueFormatter(datum.secondaryValue ?? 0);

          if (datum.secondaryValue !== undefined) {
            bars.push(
              <rect
                key="secondary"
                x={groupCenter - barSlot}
                y={PADDING.top + plotHeight - secondaryHeight}
                width={barSlot}
                height={secondaryHeight}
                rx="3"
                fill={secondaryColorValue}
              >
                <title>{`${datum.label}: total ${formattedSecondary}`}</title>
              </rect>,
            );
            bars.push(
              <rect
                key="primary"
                x={groupCenter}
                y={PADDING.top + plotHeight - primaryHeight}
                width={barSlot}
                height={primaryHeight}
                rx="3"
                fill={primaryColorValue}
              >
                <title>{`${datum.label}: completed ${formattedValue}`}</title>
              </rect>,
            );
          } else {
            bars.push(
              <rect
                key="primary"
                x={groupCenter - barSlot / 2}
                y={PADDING.top + plotHeight - primaryHeight}
                width={barSlot}
                height={primaryHeight}
                rx="3"
                fill={primaryColorValue}
              >
                <title>{`${datum.label}: ${formattedValue}`}</title>
              </rect>,
            );
          }

          if (showValueLabels && datum.value > 0) {
            bars.push(
              <text
                key="value-label"
                x={groupCenter}
                y={PADDING.top + plotHeight - primaryHeight - 6}
                textAnchor="middle"
                className="fill-muted-foreground"
                fontSize="10"
              >
                {formattedValue}
              </text>,
            );
          }

          return (
            <g key={datum.label}>
              {bars}
              <text
                x={groupCenter}
                y={height - 12}
                textAnchor="middle"
                className="fill-muted-foreground"
                fontSize="10"
              >
                {datum.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
