"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";
import { FloatingNavbar } from "@/components/landing/floating-navbar";
import { Hero } from "@/components/landing/hero";
import { StatsStrip } from "@/components/landing/stats-strip";
import { FeaturesBento } from "@/components/landing/features-bento";
import { HowItWorks } from "@/components/landing/how-it-works";
import { TrustSection } from "@/components/landing/trust-section";
import { CtaSection } from "@/components/landing/cta-section";
import { LandingFooter } from "@/components/landing/landing-footer";

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading || user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <FloatingNavbar />
      <main>
        <Hero />
        <StatsStrip />
        <FeaturesBento />
        <HowItWorks />
        <TrustSection />
        <CtaSection />
      </main>
      <LandingFooter />
    </div>
  );
}
