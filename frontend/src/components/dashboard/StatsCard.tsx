import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  label: string;
  value: string;
  helper?: string;
  icon: ReactNode;
  className?: string;
}

export function StatsCard({ label, value, helper, icon, className }: StatsCardProps) {
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
          <div className="rounded-2xl bg-primary/10 p-3 text-primary">{icon}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
