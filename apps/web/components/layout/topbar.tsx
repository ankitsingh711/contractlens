"use client";

import { LogOut, Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/hooks/use-auth";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/documents": "Documents",
  "/analysis": "Analysis",
  "/assistant": "AI Assistant",
  "/evaluations": "Evaluations",
  "/agent-runs": "Agent Runs",
  "/settings": "Settings",
};

export function Topbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const title =
    Object.entries(TITLES).find(([href]) => pathname.startsWith(href))?.[1] ?? "ContractLens AI";

  useEffect(() => {
    document.title = title === "ContractLens AI" ? title : `${title} · ContractLens AI`;
  }, [title]);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background px-4">
      <div className="flex items-center gap-3">
        <Sheet>
          <SheetTrigger
            render={<Button variant="ghost" size="icon" className="md:hidden" aria-label="Open navigation menu" />}
          >
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SidebarNav />
          </SheetContent>
        </Sheet>
        <h1 className="text-sm font-semibold">{title}</h1>
      </div>
      <div className="flex items-center gap-1">
        <ThemeToggle />
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger
              render={<Button variant="ghost" className="flex items-center gap-2 px-2" />}
            >
              <Avatar className="h-7 w-7">
                <AvatarFallback className="text-xs">{initials(user.full_name)}</AvatarFallback>
              </Avatar>
              <span className="hidden text-sm font-medium sm:inline">{user.full_name}</span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <p className="text-sm font-medium">{user.full_name}</p>
                <p className="text-xs font-normal text-muted-foreground">{user.email}</p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}
