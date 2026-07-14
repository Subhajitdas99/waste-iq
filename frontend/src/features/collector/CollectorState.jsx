import { WifiOff } from "lucide-react";

import { Card } from "../../components/ui/card";

export function getCollectorErrorCopy(error, fallback = "Unable to load collector data.") {
  if (!error?.response) {
    return {
      title: "No internet",
      description: "We could not reach Waste-IQ. Check your connection and try again."
    };
  }

  if (error.response.status >= 500) {
    return {
      title: "Server error",
      description: "Waste-IQ is having trouble loading this collector data. Please try again shortly."
    };
  }

  return {
    title: "Unable to load",
    description: error.response.data?.detail || fallback
  };
}

export function CollectorErrorState({ error, title, fallback }) {
  const copy = getCollectorErrorCopy(error, fallback);

  return (
    <Card className="border-coral/30 bg-coral/10 p-5" role="alert">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/70 text-coral">
          <WifiOff className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-coral">{title || copy.title}</p>
          <p className="mt-3 text-sm leading-6 text-ink/70">{copy.description}</p>
        </div>
      </div>
    </Card>
  );
}

export function CollectorEmptyState({ title, description }) {
  return (
    <Card className="p-8 text-center">
      <p className="font-display text-2xl text-ink">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-ink/60">{description}</p>
    </Card>
  );
}
