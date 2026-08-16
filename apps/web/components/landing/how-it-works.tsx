import { Bot, ShieldCheck, UploadCloud } from "lucide-react";

const STEPS = [
  {
    icon: UploadCloud,
    title: "Upload your contracts",
    description: "PDF, DOCX, or TXT. Documents are parsed, chunked by clause and heading, and embedded.",
  },
  {
    icon: Bot,
    title: "Ask the agent anything",
    description: "The LangGraph agent plans, retrieves evidence with hybrid search, and reasons over what it finds.",
  },
  {
    icon: ShieldCheck,
    title: "Get a cited answer — or an honest no",
    description: "Every claim links to a real clause. Below the evidence threshold, it abstains instead of guessing.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-24">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">How it works</h2>
        <p className="mt-4 text-muted-foreground">Three steps from a raw contract to a grounded, traceable answer.</p>
      </div>

      <div className="relative mt-16 grid grid-cols-1 gap-10 sm:grid-cols-3">
        <div
          aria-hidden
          className="absolute top-6 right-[16.5%] left-[16.5%] hidden h-px bg-gradient-to-r from-primary/40 via-mint/60 to-primary/40 sm:block"
        />
        {STEPS.map((step, i) => (
          <div key={step.title} className="relative flex flex-col items-center text-center sm:items-start sm:text-left">
            <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2 border-primary bg-background text-primary shadow-sm">
              <step.icon className="h-5 w-5" />
            </div>
            <span className="mt-4 font-mono text-xs text-mint">STEP {i + 1}</span>
            <h3 className="mt-1 text-lg font-semibold text-foreground">{step.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
