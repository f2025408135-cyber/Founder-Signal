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
    <aside className="w-14 shrink-0 border-r border-border bg-card/90 flex flex-col h-full sm:w-56" style={{ boxShadow: "inset -1px 0 0 rgba(0,0,0,.4), 12px 0 32px -24px rgba(0,0,0,.9)" }}>
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="metal-button w-7 h-7 rounded-sm flex items-center justify-center">
            <Activity className="w-4 h-4" />
          </div>
          <div className="hidden sm:block">
            <div className="text-sm font-bold leading-tight text-text-primary">
              Founder Signal
            </div>
            <div className="technical-label text-text-muted">
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
                "flex items-center justify-center gap-3 px-3 py-2 rounded-sm border text-sm transition-all sm:justify-start",
                active
                  ? "border-border-accent bg-elevated/90 text-text-primary font-medium shadow-[inset_0_1px_0_rgba(240,244,248,.12)]"
                  : "border-transparent text-text-muted hover:border-border-strong hover:bg-elevated/70 hover:text-text-primary"
              )}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="hidden px-4 py-3 border-t border-border text-[10px] text-text-subtle sm:block">
        Maschmeyer Group · $100K check
      </div>
    </aside>
  );
}
