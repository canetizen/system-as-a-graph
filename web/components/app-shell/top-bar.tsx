"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";

import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ContextSwitcher } from "./context-switcher";
import { NAV_GROUPS } from "./nav-groups";
import { ThemeToggle } from "./theme-toggle";

function PipelineDot({ readiness }: { readiness: "muted" | "conforming" }) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-block h-1.5 w-1.5 rounded-full",
        readiness === "conforming" ? "bg-status-conforming" : "bg-muted-foreground/40",
      )}
    />
  );
}

function GroupNav() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-5">
      {NAV_GROUPS.map((group) => {
        const active = pathname === group.href || pathname.startsWith(`${group.href}/`);
        return (
          <Link
            key={group.key}
            href={group.href}
            className={cn(
              "flex items-center gap-1.5 text-sm transition-colors",
              active ? "font-semibold text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            <PipelineDot readiness={group.readiness} />
            {group.label}
          </Link>
        );
      })}
    </nav>
  );
}

function SessionMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="rounded-full outline-none focus-visible:ring-1 focus-visible:ring-ring">
        <Avatar>
          <AvatarFallback>OP</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>operator@ldap</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-6">
        <ContextSwitcher />
        <GroupNav />
      </div>
      <div className="flex items-center gap-4">
        {/* Background-job status strip (SSE) lands with Procrastinate integration */}
        <span className="text-xs text-muted-foreground">No active jobs</span>
        <ThemeToggle />
        <SessionMenu />
      </div>
    </header>
  );
}
