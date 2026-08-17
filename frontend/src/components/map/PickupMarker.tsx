import { pickupMarkerColor } from "./markerColors";

interface PickupMarkerProps {
  id: number;
  status: string;
  x: number;
  y: number;
  label: string;
  active: boolean;
  isActivePickup?: boolean;
  onClick?: (pickupId: number) => void;
}

export function PickupMarker({
  id,
  status,
  x,
  y,
  label,
  active,
  isActivePickup = false,
  onClick,
}: PickupMarkerProps) {
  const color = pickupMarkerColor(status);
  const labelId = `pickup-marker-label-${id}`;

  return (
    <g
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={`Pickup ${id} marker (${status})`}
      onClick={onClick ? () => onClick(id) : undefined}
      onKeyDown={
        onClick
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onClick(id);
              }
            }
          : undefined
      }
      className="cursor-pointer outline-none focus-visible:opacity-100"
      transform={`translate(${x}, ${y})`}
    >
      {isActivePickup ? (
        <animateTransform attributeName="transform" type="scale" values={`1;1.35;1`} dur="1.4s" repeatCount="indefinite" additive="replace" />
      ) : null}
      <circle
        r={isActivePickup ? 8 : 7}
        fill={color}
        stroke="white"
        strokeWidth={2}
        data-testid={`pickup-marker-${id}`}
        aria-hidden="true"
      />
      {active ? <circle r={11} fill={color} opacity={0.25} aria-hidden="true" /> : null}
      <text
        id={labelId}
        y={-10}
        textAnchor="middle"
        className="pointer-events-none fill-foreground text-[11px] font-semibold"
      >
        {label}
      </text>
    </g>
  );
}