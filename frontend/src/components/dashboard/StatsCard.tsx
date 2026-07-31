import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type StatsTone = "default" | "primary" | "success" | "warning" | "danger";

interface StatsCardProps {
  label: string;
  value: string;
  helper?: string;
  icon: ReactNode;
  tone?: StatsTone;
  className?: string;
}

const TONE_CLASSES: Record<StatsTone, string> = {
  default: "bg-primary/10 text-primary",
  primary: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  danger: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
};

export function StatsCard({
  label,
  value,
  helper,
  icon,
  tone = "default",
  className,
}: StatsCardProps) {
  return (
    <motion.div whileHover={{ y: -4 }} transition={{ duration: 0.2 }}>
      <Card
        className={cn(
          "border-white/40 bg-card/85 shadow-md backdrop-blur-sm",
          className,
        )}
      >
        <CardContent className="flex items-start justify-between gap-4 p-6">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className="mt-3 text-3xl font-bold tracking-tight">{value}</p>
            {helper ? (
              <p className="mt-2 text-sm text-muted-foreground">{helper}</p>
            ) : null}
          </div>
          <div className={cn("rounded-2xl p-3", TONE_CLASSES[tone])}>{icon}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
