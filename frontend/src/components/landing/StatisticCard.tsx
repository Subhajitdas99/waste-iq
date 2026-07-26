import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface StatisticCardProps {
  value: string;
  label: string;
  index?: number;
  className?: string;
}

export function StatisticCard({
  value,
  label,
  index = 0,
  className,
}: StatisticCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1 }}
      className={cn(
        "text-center space-y-2 p-6 rounded-2xl bg-card/60 backdrop-blur-sm border shadow-sm hover:shadow-md transition-shadow",
        className
      )}
    >
      <div className="text-3xl md:text-4xl font-bold text-primary">{value}</div>
      <div className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
        {label}
      </div>
    </motion.div>
  );
}
