import { COLLECTOR_MARKER_COLOR } from "./markerColors";

interface CollectorMarkerProps {
  x: number;
  y: number;
  accuracy?: number | null;
  active: boolean;
  onClick?: () => void;
}

export function CollectorMarker({ x, y, accuracy = null, active, onClick }: CollectorMarkerProps) {
  return (
    <g
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label="Your current location"
      onClick={onClick}
      onKeyDown={
        onClick
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      transform={`translate(${x}, ${y})`}
    >
      {accuracy != null && accuracy > 0 && active ? (
        <circle r={13} fill={COLLECTOR_MARKER_COLOR} opacity={0.12} data-testid="collector-accuracy-circle" />
      ) : null}
      <circle r={6} fill={COLLECTOR_MARKER_COLOR} stroke="white" strokeWidth={2} data-testid="collector-marker" />
      <circle r={2.5} fill="white" aria-hidden="true" />
    </g>
  );
}