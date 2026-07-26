import { cn } from "@/lib/utils";

export function Toast({ message, type = "default" }: { message: string, type?: "default" | "success" | "error" }) {
  return (
    <div className={cn(
      "fixed bottom-4 right-4 p-4 rounded-md shadow-md text-sm font-medium border z-50",
      type === "default" && "bg-background text-foreground",
      type === "success" && "bg-primary text-primary-foreground border-primary",
      type === "error" && "bg-destructive text-destructive-foreground border-destructive"
    )}>
      {message}
    </div>
  );
}
