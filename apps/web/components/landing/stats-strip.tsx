const STATS = [
  { value: "12", label: "risk categories scanned per contract" },
  { value: "2-way", label: "hybrid retrieval — vector + keyword, fused with RRF" },
  { value: "100%", label: "of citations traced to a retrieved clause" },
  { value: "8", label: "inspectable steps per agent run" },
];

export function StatsStrip() {
  return (
    <section className="border-y bg-muted/30">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 px-6 py-10 sm:grid-cols-4">
        {STATS.map((stat) => (
          <div key={stat.label} className="text-center sm:text-left">
            <p className="bg-gradient-to-r from-primary to-[#0aa88a] bg-clip-text text-3xl font-semibold text-transparent">
              {stat.value}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
