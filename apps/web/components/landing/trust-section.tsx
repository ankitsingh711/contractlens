import { FileClock, KeyRound, ShieldAlert, ShieldOff } from "lucide-react";

const PRINCIPLES = [
  {
    icon: ShieldOff,
    title: "Abstention over fabrication",
    description: "Evidence is scored before generation. Below threshold, the agent declines instead of guessing.",
  },
  {
    icon: ShieldAlert,
    title: "Citations are mechanically enforced",
    description: "Not a prompt instruction — a validator strips any marker that doesn't map to a retrieved chunk.",
  },
  {
    icon: FileClock,
    title: "Full audit trail",
    description: "Every upload, query, and analysis is logged with the acting user, resource, and timestamp.",
  },
  {
    icon: KeyRound,
    title: "Isolated by organization",
    description: "Every query, document, and agent run is scoped to your organization — enforced at the query layer.",
  },
];

export function TrustSection() {
  return (
    <section id="trust" className="border-y bg-muted/30">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Grounding is a guarantee, not a suggestion
          </h2>
          <p className="mt-4 text-muted-foreground">
            The parts of this system that matter most for trust aren&apos;t prompted — they&apos;re enforced in code.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {PRINCIPLES.map((item) => (
            <div key={item.title} className="rounded-2xl border bg-card p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-mint/15 text-accent-foreground">
                <item.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-foreground">{item.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
