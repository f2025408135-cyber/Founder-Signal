"use client";
import { cn } from "@/lib/utils";

export function Topbar({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "glass sticky top-0 z-30 border-b border-border px-6 py-3 flex items-center justify-between",
        className
      )}
    >
      {children}
    </div>
  );
}
