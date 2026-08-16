"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { LogoWordmark } from "@/components/landing/logo-mark";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "#capabilities", label: "Capabilities" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#trust", label: "Trust & grounding" },
];

export function FloatingNavbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <div className="flex w-full max-w-5xl items-center justify-between gap-3">
        {/* Logo pill — floats independently from the nav/actions pill */}
        <Link
          href="/"
          className={cn(
            "flex items-center rounded-full border px-3 py-2 shadow-sm backdrop-blur-md transition-colors",
            scrolled ? "border-border bg-card/80" : "border-transparent bg-card/50"
          )}
        >
          <LogoWordmark className="text-sm" />
        </Link>

        {/* Nav + actions pill */}
        <div
          className={cn(
            "hidden items-center gap-1 rounded-full border px-1.5 py-1.5 shadow-sm backdrop-blur-md transition-colors md:flex",
            scrolled ? "border-border bg-card/80" : "border-transparent bg-card/50"
          )}
        >
          <nav className="flex items-center gap-1 px-1">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mx-1 h-5 w-px bg-border" />
          <Button variant="ghost" size="sm" className="rounded-full" render={<Link href="/login" />}>
            Log in
          </Button>
          <Button
            size="sm"
            className="rounded-full bg-gradient-to-r from-primary to-[#0a8fbf] text-white hover:opacity-90"
            render={<Link href="/register" />}
          >
            Get started
          </Button>
        </div>

        {/* Mobile trigger */}
        <button
          type="button"
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((o) => !o)}
          className={cn(
            "flex h-11 w-11 items-center justify-center rounded-full border shadow-sm backdrop-blur-md transition-colors md:hidden",
            scrolled ? "border-border bg-card/80" : "border-transparent bg-card/50"
          )}
        >
          {mobileOpen ? <X className="h-4.5 w-4.5" /> : <Menu className="h-4.5 w-4.5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="absolute inset-x-4 top-16 rounded-2xl border bg-card/95 p-4 shadow-lg backdrop-blur-md md:hidden">
          <nav className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mt-3 flex gap-2 border-t pt-3">
            <Button variant="outline" className="flex-1" render={<Link href="/login" />}>
              Log in
            </Button>
            <Button
              className="flex-1 bg-gradient-to-r from-primary to-[#0a8fbf] text-white"
              render={<Link href="/register" />}
            >
              Get started
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
