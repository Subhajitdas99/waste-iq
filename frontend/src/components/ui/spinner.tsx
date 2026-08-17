import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  size?: number;
  label?: string;
}

export function Spinner({ className, size = 24, label = "Loading" }: SpinnerProps) {
  return (
    <span role="status" aria-label={label} className="inline-flex">
      <Loader2
        size={size}
        className={cn("animate-spin text-primary", className)}
        aria-hidden="true"
      />
    </span>
  );
}

export function LoadingScreen() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background">
      <Spinner size={48} label="Loading Waste-IQ" />
      <p className="mt-4 animate-pulse text-muted-foreground">Loading Waste-IQ...</p>
    </div>
  );
}
