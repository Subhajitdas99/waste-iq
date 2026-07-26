import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  size?: number;
}

export function Spinner({ className, size = 24 }: SpinnerProps) {
  return (
    <Loader2 
      size={size} 
      className={cn("animate-spin text-primary", className)} 
    />
  );
}

export function LoadingScreen() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background">
      <Spinner size={48} />
      <p className="mt-4 text-muted-foreground animate-pulse">Loading Waste-IQ...</p>
    </div>
  );
}
