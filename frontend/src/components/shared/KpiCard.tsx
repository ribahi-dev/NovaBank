// Carte KPI premium : icône en médaillon dégradé, apparition en cascade.
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: LucideIcon;
  index?: number;
  danger?: boolean;
  onClick?: () => void;
}

export function KpiCard({ label, value, sub, icon: Icon, index = 0, danger, onClick }: KpiCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35, ease: "easeOut" }}
      whileHover={{ y: -3 }}
    >
      <Card
        glass
        onClick={onClick}
        className={cn("flex items-center gap-4", onClick && "cursor-pointer")}
      >
        <div
          className={cn(
            "grid h-11 w-11 shrink-0 place-items-center rounded-xl text-white",
            danger ? "bg-danger" : "bg-brand-gradient"
          )}
        >
          <Icon size={20} />
        </div>
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {label}
          </div>
          <div className={cn("mt-0.5 text-2xl font-bold", danger && "text-danger")}>{value}</div>
          {sub && <div className="truncate text-xs text-muted-foreground">{sub}</div>}
        </div>
      </Card>
    </motion.div>
  );
}
