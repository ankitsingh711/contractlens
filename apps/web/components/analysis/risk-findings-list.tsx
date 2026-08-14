import { RiskFindingCard } from "@/components/analysis/risk-finding-card";
import type { RiskFinding, RiskSeverity } from "@/types/risk-analysis";

const GROUPS: { severity: RiskSeverity; label: string }[] = [
  { severity: "high", label: "High Risk" },
  { severity: "medium", label: "Medium Risk" },
  { severity: "low", label: "Low Risk" },
];

export function RiskFindingsList({ findings }: { findings: RiskFinding[] }) {
  return (
    <div className="space-y-5">
      {GROUPS.map((group) => {
        const items = findings.filter((f) => f.severity === group.severity);
        if (items.length === 0) return null;
        return (
          <div key={group.severity} className="space-y-2">
            <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              {group.label} ({items.length})
            </h3>
            <div className="space-y-2">
              {items.map((finding) => (
                <RiskFindingCard key={finding.id} finding={finding} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
