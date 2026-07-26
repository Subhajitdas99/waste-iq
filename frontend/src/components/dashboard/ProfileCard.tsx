import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ProfileCardItem {
  label: string;
  value: string;
}

interface ProfileCardProps {
  title: string;
  description?: string;
  items: ProfileCardItem[];
  actions?: ReactNode;
}

export function ProfileCard({
  title,
  description,
  items,
  actions,
}: ProfileCardProps) {
  return (
    <Card className="border-white/40 bg-card/85 shadow-sm">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>{title}</CardTitle>
          {description ? (
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
        {actions}
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <div key={item.label} className="rounded-2xl bg-muted/40 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {item.label}
            </p>
            <p className="mt-2 font-medium">{item.value}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
