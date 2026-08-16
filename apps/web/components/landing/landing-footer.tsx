import Link from "next/link";

import { LogoWordmark } from "@/components/landing/logo-mark";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "Capabilities", href: "#capabilities" },
      { label: "How it works", href: "#how-it-works" },
      { label: "Trust & grounding", href: "#trust" },
    ],
  },
  {
    title: "Account",
    links: [
      { label: "Log in", href: "/login" },
      { label: "Get started", href: "/register" },
    ],
  },
];

export function LandingFooter() {
  return (
    <footer className="border-t">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-col justify-between gap-10 sm:flex-row">
          <div className="max-w-xs">
            <LogoWordmark />
            <p className="mt-3 text-sm text-muted-foreground">
              A citation-grounded contract intelligence agent — built to abstain rather than guess.
            </p>
          </div>
          <div className="flex gap-16">
            {COLUMNS.map((col) => (
              <div key={col.title}>
                <p className="text-sm font-semibold text-foreground">{col.title}</p>
                <ul className="mt-3 space-y-2">
                  {col.links.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-2 border-t pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} ContractLens AI. All rights reserved.</p>
          <p>Demo/portfolio project — not legal advice.</p>
        </div>
      </div>
    </footer>
  );
}
