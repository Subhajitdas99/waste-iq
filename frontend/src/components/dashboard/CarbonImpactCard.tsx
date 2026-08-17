import type { ReactNode } from "react";
import { Leaf, Newspaper, Recycle, Sprout } from "lucide-react";
import type { CarbonSavings } from "@/types/analytics";
import { formatImpactNumber } from "@/lib/recycling";
import { cn } from "@/lib/utils";

interface CarbonImpactCardProps {
  data: CarbonSavings | null;
  className?: string;
}

function ImpactTile({
  icon,
  label,
  value,
  helper,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  helper?: string;
}) {
  return (
    <div className="rounded-2xl border bg-muted/20 p-5">
      <div className="flex items-center gap-2 text-sm font-medium">
        {icon}
        {label}
      </div>
      <p className="mt-3 text-3xl font-bold tracking-tight">{value}</p>
      {helper ? (
        <p className="mt-2 text-sm text-muted-foreground">{helper}</p>
      ) : null}
    </div>
  );
}

export function CarbonImpactCard({ data, className }: CarbonImpactCardProps) {
  const hasImpact =
    data !== null &&
    (data.estimated_co2_saved > 0 ||
      data.trees_equivalent > 0 ||
      data.plastic_recycled > 0 ||
      data.paper_recycled > 0);

  if (!hasImpact || data === null) {
    return (
      <div className="rounded-2xl border border-dashed bg-muted/20 px-4 py-8 text-center text-sm text-muted-foreground">
        Carbon savings appear once completed pickups report collected weights.
      </div>
    );
  }

  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-4", className)}>
      <ImpactTile
        icon={<Leaf className="h-4 w-4 text-emerald-500" />}
        label="Estimated CO₂ Saved"
        value={`${formatImpactNumber(data.estimated_co2_saved)} kg`}
        helper="Using ~0.42 kg CO₂e saved per kg recycled"
      />
      <ImpactTile
        icon={<Sprout className="h-4 w-4 text-emerald-500" />}
        label="Trees Equivalent"
        value={formatImpactNumber(data.trees_equivalent)}
        helper="Based on ~21 kg CO₂ absorbed per tree per year"
      />
      <ImpactTile
        icon={<Recycle className="h-4 w-4 text-sky-500" />}
        label="Plastic Recycled"
        value={`${formatImpactNumber(data.plastic_recycled)} kg`}
      />
      <ImpactTile
        icon={<Newspaper className="h-4 w-4 text-violet-500" />}
        label="Paper Recycled"
        value={`${formatImpactNumber(data.paper_recycled)} kg`}
      />
    </div>
  );
}
