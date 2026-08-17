import { cn } from "@/lib/utils";
import type { NotificationStatus } from "@/types/notification";

export type NotificationFilterValue = "all" | NotificationStatus;

const NOTIFICATION_FILTER_OPTIONS: { value: NotificationFilterValue; label: string }[] = [
  { value: "all", label: "All" },
  { value: "unread", label: "Unread" },
  { value: "read", label: "Read" },
];

interface NotificationFilterProps {
  value: NotificationFilterValue;
  onChange: (value: NotificationFilterValue) => void;
}

export function NotificationFilter({ value, onChange }: NotificationFilterProps) {
  return (
    <div className="inline-flex rounded-lg border bg-muted/40 p-1" role="group" aria-label="Filter notifications">
      {NOTIFICATION_FILTER_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={cn(
            "rounded-md px-4 py-1.5 text-sm font-medium transition-colors",
            value === option.value
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-pressed={value === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}