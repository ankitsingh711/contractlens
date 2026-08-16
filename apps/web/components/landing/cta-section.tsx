import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

export function CtaSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary via-[#0c8fae] to-[#0aa88a] px-8 py-16 text-center sm:px-16">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,color-mix(in_oklch,var(--mint),transparent_60%),transparent_60%)]"
        />
        <h2 className="relative text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          See a grounded answer for yourself
        </h2>
        <p className="relative mx-auto mt-4 max-w-xl text-white/85">
          Spin up a workspace, upload a contract, and watch the agent cite its evidence in real time — no credit
          card required.
        </p>
        <div className="relative mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button
            size="lg"
            className="h-11 rounded-full bg-white px-6 text-base text-primary hover:bg-white/90"
            render={<Link href="/register" />}
          >
            Get started free
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="h-11 rounded-full border-white/30 bg-transparent px-6 text-base text-white hover:bg-white/10"
            render={<Link href="/login" />}
          >
            Log in
          </Button>
        </div>
      </div>
    </section>
  );
}
