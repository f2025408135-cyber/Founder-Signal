"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Inbox, Network, Filter, FileText, Activity, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/hero", label: "Fin", icon: Sparkles },
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/network", label: "Network", icon: Network },
  { href: "/funnel", label: "Funnel", icon: Filter },
  { href: "/thesis", label: "Thesis", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 border-r border-border bg-card flex flex-col h-full">
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-bold leading-tight text-text-primary">
              Founder Signal
            </div>
            <div className="text-[10px] text-text-subtle uppercase tracking-wider">
              VC Brain
            </div>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-2 py-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-elevated text-text-primary font-medium"
                  : "text-text-muted hover:text-text-primary hover:bg-elevated"
              )}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-border text-[10px] text-text-subtle">
        Maschmeyer Group · $100K check
      </div>
    </aside>
  );
}
