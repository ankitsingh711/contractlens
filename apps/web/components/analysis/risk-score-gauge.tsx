import { cn } from "@/lib/utils";

function bandFor(score: number) {
  if (score >= 67) return { label: "High Risk", color: "text-destructive" };
  if (score >= 34) return { label: "Medium Risk", color: "text-amber-600 dark:text-amber-500" };
  return { label: "Low Risk", color: "text-emerald-600 dark:text-emerald-500" };
}

export function RiskScoreGauge({ score }: { score: number }) {
  const band = bandFor(score);
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-4">
      <div className={cn("text-4xl font-bold tabular-nums", band.color)}>{score}</div>
      <div className="text-xs text-muted-foreground">out of 100</div>
      <div className={cn("mt-1 text-sm font-medium", band.color)}>{band.label}</div>
    </div>
  );
}
