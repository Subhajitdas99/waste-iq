import { useEffect, useMemo } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { MapContainer, Marker, Polyline, Popup, TileLayer, ZoomControl, useMap } from "react-leaflet";

import StatusBadge from "../StatusBadge";
import { Card } from "../ui/card";
import { formatDateTime, formatRequestStatus } from "../../utils/pickupRequests";
import { useBrowserGeolocation } from "../../hooks/useBrowserGeolocation";

const DEFAULT_CENTER = [22.5726, 88.3639];
const CLUSTER_THRESHOLD = 12;

const statusColors = {
  pending: "#f59e0b",
  accepted: "#0ea5e9",
  on_the_way: "#6366f1",
  collected: "#14b8a6",
  completed: "#10b981"
};

function normalizeStatus(status) {
  return String(status || "pending").toLowerCase().replaceAll(" ", "_").replaceAll("-", "_");
}

function getCoordinate(value) {
  const coordinate = Number(value);
  return Number.isFinite(coordinate) ? coordinate : null;
}

function getPickupPosition(pickup) {
  const latitude = getCoordinate(pickup?.latitude);
  const longitude = getCoordinate(pickup?.longitude);

  if (latitude === null || longitude === null) {
    return null;
  }

  return [latitude, longitude];
}

function getMarkerIcon(status, selected = false) {
  const normalizedStatus = normalizeStatus(status);
  const color = statusColors[normalizedStatus] || "#64748b";

  return L.divIcon({
    className: `pickup-map-marker${selected ? " pickup-map-marker-selected" : ""}`,
    html: `<span style="--marker-color:${color}" aria-hidden="true"></span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14]
  });
}

function getCollectorIcon() {
  return L.divIcon({
    className: "pickup-map-marker pickup-map-marker-collector",
    html: '<span aria-hidden="true"></span>',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -16]
  });
}

function getPickupLabel(pickup) {
  return `Request #${pickup.id}${pickup.waste_type ? ` - ${pickup.waste_type}` : ""}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function FitMapBounds({ locations }) {
  const map = useMap();

  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 0);

    if (locations.length === 0) {
      map.setView(DEFAULT_CENTER, 12);
      return;
    }

    if (locations.length === 1) {
      map.setView(locations[0], 14);
      return;
    }

    map.fitBounds(L.latLngBounds(locations), {
      maxZoom: 14,
      padding: [32, 32]
    });
  }, [locations, map]);

  return null;
}

function PickupPopup({ pickup }) {
  return (
    <div className="min-w-48 space-y-2">
      <p className="font-semibold text-ink">{getPickupLabel(pickup)}</p>
      <StatusBadge status={pickup.status} />
      {pickup.map_group ? (
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink/50">
          {pickup.map_group === "assigned" ? "Assigned job" : "Available job"}
        </p>
      ) : null}
      <p className="text-xs leading-5 text-ink/70">{pickup.address || "Address not available"}</p>
      <p className="text-xs text-ink/60">{formatDateTime(pickup.created_at)}</p>
    </div>
  );
}

function createPopupHtml(pickup) {
  return `
    <div class="min-w-48 space-y-2">
      <p class="font-semibold text-ink">${escapeHtml(getPickupLabel(pickup))}</p>
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-ink/60">${escapeHtml(formatRequestStatus(pickup.status))}</p>
      ${pickup.map_group ? `<p class="text-xs font-semibold uppercase tracking-[0.18em] text-ink/50">${escapeHtml(pickup.map_group === "assigned" ? "Assigned job" : "Available job")}</p>` : ""}
      <p class="text-xs leading-5 text-ink/70">${escapeHtml(pickup.address || "Address not available")}</p>
      <p class="text-xs text-ink/60">${escapeHtml(formatDateTime(pickup.created_at))}</p>
    </div>
  `;
}

function PickupClusterLayer({ pickups, onPickupSelect, selectedPickupId }) {
  const map = useMap();

  useEffect(() => {
    const clusterGroup = L.markerClusterGroup({
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      iconCreateFunction(cluster) {
        return L.divIcon({
          className: "pickup-map-cluster",
          html: `<span>${cluster.getChildCount()}</span>`,
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        });
      }
    });

    pickups.forEach((pickup) => {
      const position = getPickupPosition(pickup);

      if (!position) {
        return;
      }

      L.marker(position, {
        icon: getMarkerIcon(pickup.status, pickup.id === selectedPickupId),
        title: getPickupLabel(pickup)
      })
        .on("click", () => onPickupSelect?.(pickup))
        .bindPopup(createPopupHtml(pickup))
        .addTo(clusterGroup);
    });

    map.addLayer(clusterGroup);

    return () => {
      map.removeLayer(clusterGroup);
    };
  }, [map, onPickupSelect, pickups, selectedPickupId]);

  return null;
}

function getCollectorPosition(collectorLocation, browserPosition) {
  if (collectorLocation) {
    const latitude = getCoordinate(collectorLocation.latitude ?? collectorLocation.lat);
    const longitude = getCoordinate(collectorLocation.longitude ?? collectorLocation.lng);

    return latitude === null || longitude === null ? null : [latitude, longitude];
  }

  if (!browserPosition) {
    return null;
  }

  return [browserPosition.latitude, browserPosition.longitude];
}

export default function PickupMap({
  pickups = [],
  collectorLocation = null,
  collectorLocationError: externalCollectorLocationError = "",
  collectorLocationLoading: externalCollectorLocationLoading = false,
  onRetryCollectorLocation,
  onPickupSelect,
  selectedPickupId = null,
  showCollectorLocation = false,
  title = "Pickup locations",
  description = "Track pickup requests by current status.",
  useBrowserCollectorLocation = true,
  className = ""
}) {
  const {
    error: collectorLocationError,
    isLocating: isCollectorLocating,
    position: browserCollectorPosition,
    requestLocation: retryCollectorLocation
  } = useBrowserGeolocation({
    enabled: showCollectorLocation && useBrowserCollectorLocation && !collectorLocation,
    watch: true,
    errorTitle: "Collector location unavailable"
  });
  const activeCollectorLocationError = externalCollectorLocationError || collectorLocationError;
  const activeCollectorLocationLoading = externalCollectorLocationLoading || isCollectorLocating;
  const handleRetryCollectorLocation = onRetryCollectorLocation || retryCollectorLocation;
  const validPickups = useMemo(
    () => pickups.filter((pickup) => Boolean(getPickupPosition(pickup))),
    [pickups]
  );
  const collectorPosition = getCollectorPosition(collectorLocation, browserCollectorPosition);
  const selectedPickup = validPickups.find((pickup) => pickup.id === selectedPickupId) || null;
  const selectedPickupPosition = selectedPickup ? getPickupPosition(selectedPickup) : null;
  const routePositions = collectorPosition && selectedPickupPosition ? [collectorPosition, selectedPickupPosition] : [];
  const locations = useMemo(
    () => [
      ...validPickups.map((pickup) => getPickupPosition(pickup)),
      ...(collectorPosition ? [collectorPosition] : [])
    ],
    [collectorPosition, validPickups]
  );
  const shouldCluster = validPickups.length >= CLUSTER_THRESHOLD;

  return (
    <section className={`glass-panel overflow-hidden rounded-[2rem] border border-white/60 shadow-glow ${className}`}>
      <div className="flex flex-col gap-4 px-5 py-5 sm:px-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Map</p>
          <h2 className="mt-2 font-display text-3xl text-ink">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">{description}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {Object.entries(statusColors).map(([status, color]) => (
            <span
              key={status}
              className="inline-flex items-center gap-2 rounded-full bg-white/75 px-3 py-2 text-xs font-semibold text-ink/70"
            >
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
              {formatRequestStatus(status)}
            </span>
          ))}
        </div>
      </div>

      {showCollectorLocation ? (
        <div className="flex flex-col gap-3 border-t border-white/60 bg-white/45 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p className="text-sm font-medium text-ink/75">
            {activeCollectorLocationLoading
              ? "Detecting collector location..."
              : collectorPosition
                ? "Collector location is active."
                : activeCollectorLocationError || "Collector location has not been shared yet."}
          </p>
          {!collectorPosition || activeCollectorLocationError ? (
            <button
              type="button"
              onClick={handleRetryCollectorLocation}
              disabled={activeCollectorLocationLoading}
              className="inline-flex items-center justify-center rounded-2xl bg-leaf px-4 py-2.5 text-sm font-semibold text-sand transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-60"
            >
              {activeCollectorLocationLoading ? "Finding location..." : "Retry location"}
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="relative h-[24rem] min-h-[18rem] w-full sm:h-[32rem]">
        {locations.length > 0 ? (
          <MapContainer
            center={locations[0]}
            zoom={13}
            zoomControl={false}
            scrollWheelZoom
            className="h-full w-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ZoomControl position="bottomright" />
            <FitMapBounds locations={locations} />

            {routePositions.length === 2 ? (
              <Polyline
                positions={routePositions}
                pathOptions={{ color: "#13231b", weight: 5, opacity: 0.8, dashArray: "10 10" }}
              />
            ) : null}

            {shouldCluster ? (
              <PickupClusterLayer
                pickups={validPickups}
                onPickupSelect={onPickupSelect}
                selectedPickupId={selectedPickupId}
              />
            ) : (
              validPickups.map((pickup) => (
                <Marker
                  key={pickup.id}
                  position={getPickupPosition(pickup)}
                  icon={getMarkerIcon(pickup.status, pickup.id === selectedPickupId)}
                  title={getPickupLabel(pickup)}
                  eventHandlers={{
                    click: () => onPickupSelect?.(pickup)
                  }}
                >
                  <Popup>
                    <PickupPopup pickup={pickup} />
                  </Popup>
                </Marker>
              ))
            )}

            {collectorPosition ? (
              <Marker position={collectorPosition} icon={getCollectorIcon()} title="Collector location">
                <Popup>
                  <div className="space-y-1">
                    <p className="font-semibold text-ink">Collector location</p>
                    <p className="text-xs text-ink/70">Current browser location</p>
                  </div>
                </Popup>
              </Marker>
            ) : null}
          </MapContainer>
        ) : (
          <Card className="m-5 flex h-[calc(100%-2.5rem)] items-center justify-center border-dashed border-ink/15 bg-white/70 p-6 text-center">
            <div>
              <p className="font-display text-2xl text-ink">No mapped pickups yet</p>
              <p className="mt-2 text-sm text-ink/70">Pickup requests with coordinates will appear here.</p>
            </div>
          </Card>
        )}

        {selectedPickup ? (
          <div className="pointer-events-none absolute left-4 top-4 z-[400] max-w-[calc(100%-2rem)] rounded-3xl border border-white/70 bg-white/90 p-4 shadow-glow backdrop-blur sm:max-w-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-leaf/70">Selected Job</p>
            <p className="mt-2 font-semibold text-ink">{getPickupLabel(selectedPickup)}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge status={selectedPickup.status} />
              {selectedPickup.map_group ? (
                <span className="rounded-full bg-sand/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-ink/60">
                  {selectedPickup.map_group === "assigned" ? "Assigned" : "Available"}
                </span>
              ) : null}
            </div>
            {routePositions.length === 2 ? (
              <p className="mt-3 text-xs font-medium text-ink/65">Current route shown from collector to pickup.</p>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
