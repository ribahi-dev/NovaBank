// Pastille de score 0-100 : la couleur EST l'information.
import { scoreTone } from "@/lib/format";
import { cn } from "@/lib/utils";

const TONES: Record<string, string> = {
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  critical: "bg-critical",
};

export function ScoreBadge({ score }: { score?: number | null }) {
  if (score === null || score === undefined)
    return <span className="text-muted-foreground">—</span>;
  return (
    <span
      className={cn(
        "inline-flex min-w-[46px] items-center justify-center rounded-lg px-2.5 py-1 text-[13px] font-bold text-white",
        TONES[scoreTone(score)]
      )}
    >
      {score}
    </span>
  );
}
