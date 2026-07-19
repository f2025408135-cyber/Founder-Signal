import * as React from "react";
import { cn } from "@/lib/utils";

// Re-export Button from button.tsx
export { Button } from "./button";
export type { ButtonProps } from "./button";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "metal-panel rounded-sm text-text-primary",
        className
      )}
      {...props}
    />
  );
}

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "outline" | "secondary" | "success" | "warning" | "error";
}) {
  const variants = {
    default: "bg-accent/10 text-text-primary border-border-accent",
    outline: "border border-border-strong bg-canvas-base/30 text-text-secondary",
    secondary: "bg-elevated/70 text-text-secondary border-border-strong",
    success: "bg-success-bg text-text-primary border-success-border",
    warning: "bg-warning-bg text-text-primary border-warning-border",
    error: "bg-error-bg text-text-primary border-error-border",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm px-2 py-0.5 text-[10px] font-medium leading-none border",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "metal-input h-9 w-full rounded-sm border border-border-strong px-3 py-1 text-sm text-text-primary transition-colors placeholder:text-text-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "metal-input min-h-[80px] w-full rounded-sm border border-border-strong px-3 py-2 text-sm text-text-primary transition-colors placeholder:text-text-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export function Separator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("h-px bg-border", className)} {...props} />;
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded-md bg-elevated", className)} />;
}

// 10-segment progress bar per spec §9.1
export function Progress({
  value,
  className,
  color = "text-accent",
}: {
  value: number;
  className?: string;
  color?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const filledCount = Math.round(clamped / 10);
  return (
    <span className={cn("inline-flex items-center", color, className)}>
      {Array.from({ length: 10 }).map((_, i) => (
        <span
          key={i}
          className={cn(
            "inline-block w-[6px] h-[10px] mr-[2px] rounded-[1px]",
            i < filledCount ? "bg-current" : "bg-elevated"
          )}
        />
      ))}
    </span>
  );
}
