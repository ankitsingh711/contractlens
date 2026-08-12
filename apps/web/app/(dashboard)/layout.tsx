"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Topbar } from "@/components/layout/topbar";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Loading workspace...
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="hidden w-64 shrink-0 border-r md:block">
        <SidebarNav />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-muted/20 p-6">{children}</main>
      </div>
    </div>
  );
}
