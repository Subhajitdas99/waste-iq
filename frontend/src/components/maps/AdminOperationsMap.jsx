import { useEffect, useMemo, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { MapContainer, TileLayer, ZoomControl, useMap } from "react-leaflet";

import { Card } from "../ui/card";
import { formatDateTime, formatRequestStatus } from "../../utils/pickupRequests";

const DEFAULT_CENTER = [22.5726, 88.3639];

const markerConfig = {
  citizen: {
    label: "Citizens",
    color: "#29543a"
  },
  collector: {
    label: "Collectors",
    color: "#0ea5e9"
  },
  pending: {
    label: "Pending pickups",
    color: "#f59e0b"
  },
  completed: {
    label: "Completed pickups",
    color: "#10b981"
  }
};

function getCoordinate(value) {
  const coordinate = Number(value);
  return Number.isFinite(coordinate) ? coordinate : null;
}

function getRequestPosition(request) {
  const latitude = getCoordinate(request?.latitude);
  const longitude = getCoordinate(request?.longitude);

  if (latitude === null || longitude === null) {
    return null;
  }

  return [latitude, longitude];
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function createOperationIcon(type) {
  const color = markerConfig[type]?.color || "#64748b";

  return L.divIcon({
    className: `operations-map-marker operations-map-marker-${type}`,
    html: `<span style="--operations-marker-color:${color}" aria-hidden="true"></span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -15]
  });
}

function createPopupHtml(entity) {
  return `
    <div class="min-w-48 space-y-2">
      <p class="font-semibold text-ink">${escapeHtml(entity.title)}</p>
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-ink/60">${escapeHtml(entity.subtitle)}</p>
      <p class="text-xs leading-5 text-ink/70">${escapeHtml(entity.address)}</p>
      ${entity.meta ? `<p class="text-xs text-ink/60">${escapeHtml(entity.meta)}</p>` : ""}
    </div>
  `;
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
      padding: [36, 36]
    });
  }, [locations, map]);

  return null;
}

function OperationsClusterLayer({ entities }) {
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

    entities.forEach((entity) => {
      L.marker(entity.position, {
        icon: createOperationIcon(entity.type),
        title: entity.title
      })
        .bindPopup(createPopupHtml(entity))
        .addTo(clusterGroup);
    });

    map.addLayer(clusterGroup);

    return () => {
      map.removeLayer(clusterGroup);
    };
  }, [entities, map]);

  return null;
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function buildUserLocationEntities(requests) {
  const citizens = new Map();
  const collectors = new Map();

  requests.forEach((request) => {
    const position = getRequestPosition(request);

    if (!position) {
      return;
    }

    if (!citizens.has(request.user_id)) {
      citizens.set(request.user_id, {
        id: `citizen-${request.user_id}`,
        type: "citizen",
        position,
        title: request.citizen_name || "Citizen",
        subtitle: "Citizen pickup location",
        address: request.address,
        meta: `Latest request #${request.id}`
      });
    }

    if (request.assigned_collector_name && !collectors.has(request.assigned_collector_name)) {
      collectors.set(request.assigned_collector_name, {
        id: `collector-${request.assigned_collector_name}`,
        type: "collector",
        position,
        title: request.assigned_collector_name,
        subtitle: "Collector assigned pickup",
        address: request.address,
        meta: `Assigned request #${request.id}`
      });
    }
  });

  return [...citizens.values(), ...collectors.values()];
}

function buildPickupEntities(requests) {
  return requests
    .filter((request) => request.status === "pending" || request.status === "completed")
    .map((request) => {
      const position = getRequestPosition(request);

      if (!position) {
        return null;
      }

      return {
        id: `pickup-${request.id}`,
        type: request.status,
        position,
        title: `Request #${request.id} - ${request.waste_type || "Pickup"}`,
        subtitle: formatRequestStatus(request.status),
        address: request.address,
        meta: formatDateTime(request.created_at)
      };
    })
    .filter(Boolean);
}

export default function AdminOperationsMap({ requests = [], users = [] }) {
  const [statusFilter, setStatusFilter] = useState("all");
  const [wasteTypeFilter, setWasteTypeFilter] = useState("all");
  const [collectorFilter, setCollectorFilter] = useState("all");

  const wasteTypes = useMemo(() => uniqueSorted(requests.map((request) => request.waste_type)), [requests]);
  const collectors = useMemo(
    () => uniqueSorted(requests.map((request) => request.assigned_collector_name)),
    [requests]
  );
  const filteredRequests = useMemo(
    () =>
      requests.filter((request) => {
        const statusMatches = statusFilter === "all" || request.status === statusFilter;
        const wasteTypeMatches = wasteTypeFilter === "all" || request.waste_type === wasteTypeFilter;
        const collectorMatches =
          collectorFilter === "all" || request.assigned_collector_name === collectorFilter;

        return statusMatches && wasteTypeMatches && collectorMatches;
      }),
    [collectorFilter, requests, statusFilter, wasteTypeFilter]
  );
  const entities = useMemo(
    () => [...buildUserLocationEntities(filteredRequests), ...buildPickupEntities(filteredRequests)],
    [filteredRequests]
  );
  const locations = useMemo(() => entities.map((entity) => entity.position), [entities]);
  const counts = useMemo(
    () =>
      entities.reduce(
        (currentCounts, entity) => ({
          ...currentCounts,
          [entity.type]: (currentCounts[entity.type] || 0) + 1
        }),
        {}
      ),
    [entities]
  );
  const registeredCitizens = users.filter((user) => user.role === "citizen").length;
  const registeredCollectors = users.filter((user) => user.role === "collector").length;

  return (
    <section className="glass-panel overflow-hidden rounded-[2rem] border border-white/60 shadow-glow">
      <div className="flex flex-col gap-5 px-5 py-5 sm:px-6 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Live Marketplace Map</p>
          <h2 className="mt-2 font-display text-3xl text-ink">Admin operations map</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Monitor citizens, collectors, pending pickups, and completed pickups from existing marketplace data.
          </p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.2em] text-ink/45">
            {registeredCitizens} citizens registered - {registeredCollectors} collectors registered
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-3 xl:min-w-[34rem]">
          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-sm font-semibold text-ink outline-none transition focus:border-leaf"
            >
              <option value="all">All statuses</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">Waste Type</span>
            <select
              value={wasteTypeFilter}
              onChange={(event) => setWasteTypeFilter(event.target.value)}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-sm font-semibold text-ink outline-none transition focus:border-leaf"
            >
              <option value="all">All waste</option>
              {wasteTypes.map((wasteType) => (
                <option key={wasteType} value={wasteType}>
                  {wasteType}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">Collector</span>
            <select
              value={collectorFilter}
              onChange={(event) => setCollectorFilter(event.target.value)}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-sm font-semibold text-ink outline-none transition focus:border-leaf"
            >
              <option value="all">All collectors</option>
              {collectors.map((collector) => (
                <option key={collector} value={collector}>
                  {collector}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 border-y border-white/60 bg-white/45 px-5 py-4 sm:px-6">
        {Object.entries(markerConfig).map(([type, config]) => (
          <span
            key={type}
            className="inline-flex items-center gap-2 rounded-full bg-white/75 px-3 py-2 text-xs font-semibold text-ink/70"
          >
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: config.color }} />
            {config.label}: {counts[type] || 0}
          </span>
        ))}
      </div>

      <div className="relative h-[24rem] min-h-[18rem] w-full sm:h-[32rem]">
        {entities.length > 0 ? (
          <MapContainer
            center={locations[0]}
            zoom={12}
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
            <OperationsClusterLayer entities={entities} />
          </MapContainer>
        ) : (
          <Card className="m-5 flex h-[calc(100%-2.5rem)] items-center justify-center border-dashed border-ink/15 bg-white/70 p-6 text-center">
            <div>
              <p className="font-display text-2xl text-ink">No marketplace locations</p>
              <p className="mt-2 text-sm text-ink/70">Adjust filters or wait for pickup requests with coordinates.</p>
            </div>
          </Card>
        )}
      </div>
    </section>
  );
}
