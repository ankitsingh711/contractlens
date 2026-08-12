"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  ShieldAlert,
  MessagesSquare,
  ClipboardCheck,
  Bot,
  Settings,
  Scale,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useSystemStatus } from "@/hooks/use-system-status";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/analysis", label: "Analysis", icon: ShieldAlert },
  { href: "/assistant", label: "AI Assistant", icon: MessagesSquare },
  { href: "/evaluations", label: "Evaluations", icon: ClipboardCheck },
  { href: "/agent-runs", label: "Agent Runs", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function SidebarNav() {
  const pathname = usePathname();
  const { data: status } = useSystemStatus();

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Scale className="h-4 w-4" />
        </div>
        <span className="text-sm font-semibold tracking-tight">ContractLens AI</span>
      </div>
      <nav className="flex-1 space-y-0.5 p-2">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      {status?.demo_mode && (
        <div className="border-t p-3 text-xs text-muted-foreground">
          <p className="font-medium text-foreground">Demo mode</p>
          <p>Configure LLM_PROVIDER to use live models.</p>
        </div>
      )}
    </div>
  );
}
