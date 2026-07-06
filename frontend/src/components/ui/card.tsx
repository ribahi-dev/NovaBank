// Card — surface principale de l'interface (option verre : <Card glass>).
import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
}

export function Card({ className, glass, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl2 border border-border bg-card text-card-foreground p-5",
        glass ? "glass" : "shadow-[var(--shadow-soft)]",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mb-4 flex items-start justify-between gap-3", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-[15px] font-semibold", className)} {...props} />;
}
