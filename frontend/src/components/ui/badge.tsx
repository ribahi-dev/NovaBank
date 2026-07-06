// Badge — pastilles d'état colorées (statuts, niveaux, types).
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      tone: {
        neutral: "bg-muted text-muted-foreground",
        primary: "bg-primary-soft text-primary-strong dark:text-primary",
        success: "bg-success/12 text-success",
        warning: "bg-warning/12 text-warning",
        danger: "bg-danger/12 text-danger",
        critical: "bg-critical text-white",
        dark: "bg-sidebar text-white",
      },
    },
    defaultVariants: { tone: "neutral" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

// Correspondances domaine -> ton visuel (une seule source de vérité).
export const LEVEL_TONE = { low: "success", medium: "warning", high: "danger", critical: "critical" } as const;
export const STATUS_TONE = { open: "danger", in_progress: "warning", closed: "neutral" } as const;
export const ACCOUNT_TONE = { active: "success", blocked: "danger", closed: "neutral" } as const;
export const TYPE_TONE = { deposit: "success", withdrawal: "danger", transfer: "primary" } as const;
