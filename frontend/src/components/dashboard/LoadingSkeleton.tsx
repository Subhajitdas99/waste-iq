import { Skeleton } from "@/components/ui/skeleton";

interface LoadingSkeletonProps {
  variant?: "cards" | "detail";
  count?: number;
}

export function LoadingSkeleton({
  variant = "cards",
  count = 3,
}: LoadingSkeletonProps) {
  if (variant === "detail") {
    return (
      <div className="space-y-6">
        <Skeleton className="h-36 rounded-3xl" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-80 rounded-3xl" />
          <Skeleton className="h-80 rounded-3xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton key={index} className="h-52 rounded-3xl" />
      ))}
    </div>
  );
}
