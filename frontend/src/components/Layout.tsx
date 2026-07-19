/** Top-level layout — sidebar nav + main content area. */
import { Link, useLocation } from "react-router-dom";
import { Inbox, Compass, FileText, Activity } from "lucide-react";
import { cn } from "../lib/utils";

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navItems = [
    { to: "/", label: "Inbox", icon: Inbox, pattern: /^\/$/ },
    { to: "/outbound", label: "Outbound", icon: Compass, pattern: /^\/outbound/ },
    { to: "/thesis", label: "Thesis", icon: FileText, pattern: /^\/thesis/ },
  ];

  return (
    <div className="flex h-screen bg-[var(--color-background)]">
      {/* Sidebar */}
      <aside className="w-56 border-r border-[var(--color-border)] bg-[var(--color-card)] flex flex-col">
        <div className="px-5 py-5 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-[var(--color-primary)] flex items-center justify-center">
              <Activity className="w-4 h-4 text-[var(--color-primary-foreground)]" />
            </div>
            <div>
              <div className="text-sm font-semibold leading-tight">Founder Signal</div>
              <div className="text-[10px] text-[var(--color-muted-foreground)] uppercase tracking-wider">
                VC Brain
              </div>
            </div>
          </div>
        </div>
        <nav className="flex-1 px-2 py-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = item.pattern.test(location.pathname);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  active
                    ? "bg-[var(--color-secondary)] text-[var(--color-secondary-foreground)] font-medium"
                    : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-[var(--color-accent)]"
                )}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="px-4 py-3 border-t border-[var(--color-border)] text-[10px] text-[var(--color-muted-foreground)]">
          Maschmeyer Group · $100K check
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
