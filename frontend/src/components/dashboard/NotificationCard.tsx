import { BellRing } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface NotificationCardProps {
  title: string;
  message: string;
  timestamp?: string;
  unread?: boolean;
  className?: string;
}

export function NotificationCard({
  title,
  message,
  timestamp,
  unread = false,
  className,
}: NotificationCardProps) {
  return (
    <Card className={cn("border-white/40 bg-card/85 shadow-sm", className)}>
      <CardContent className="flex gap-4 p-5">
        <div className="rounded-2xl bg-primary/10 p-3 text-primary">
          <BellRing className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="font-medium">{title}</p>
            {unread ? (
              <span className="h-2.5 w-2.5 rounded-full bg-primary" aria-label="Unread" />
            ) : null}
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{message}</p>
          {timestamp ? (
            <p className="mt-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {timestamp}
            </p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
