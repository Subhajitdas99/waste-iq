import { MapPin, Scale, Truck, User } from "lucide-react";

import StatusBadge from "./StatusBadge";

export default function RequestCard({ request, actions }) {
  return (
    <div className="glass-panel rounded-3xl border border-white/60 p-5 shadow-glow">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-display text-2xl text-ink">{request.waste_type}</h3>
            <StatusBadge status={request.status} />
          </div>
          <p className="inline-flex items-center gap-2 text-sm text-ink/70">
            <User className="h-4 w-4" />
            {request.citizen_name}
          </p>
          <p className="inline-flex items-start gap-2 text-sm text-ink/70">
            <MapPin className="mt-0.5 h-4 w-4" />
            {request.address}
          </p>
          {request.assigned_collector_name ? (
            <p className="inline-flex items-center gap-2 text-sm text-ink/70">
              <Truck className="h-4 w-4" />
              Assigned collector: {request.assigned_collector_name}
            </p>
          ) : null}
          {request.assignment?.weight_kg ? (
            <p className="inline-flex items-center gap-2 text-sm text-ink/70">
              <Scale className="h-4 w-4" />
              {request.assignment.weight_kg} kg collected
            </p>
          ) : null}
          {request.photo_url ? (
            <img
              src={request.photo_url}
              alt={request.waste_type}
              className="h-44 w-full rounded-2xl object-cover sm:w-72"
            />
          ) : null}
        </div>
        {actions ? <div className="w-full max-w-sm">{actions}</div> : null}
      </div>
    </div>
  );
}
