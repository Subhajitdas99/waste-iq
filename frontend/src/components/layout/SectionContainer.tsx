import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionContainerProps {
  id?: string;
  children: ReactNode;
  className?: string;
  containerClassName?: string;
}

export function SectionContainer({
  id,
  children,
  className,
  containerClassName,
}: SectionContainerProps) {
  return (
    <section id={id} className={cn("py-20 md:py-24", className)}>
      <div className={cn("container mx-auto px-4 md:px-6", containerClassName)}>
        {children}
      </div>
    </section>
  );
}
