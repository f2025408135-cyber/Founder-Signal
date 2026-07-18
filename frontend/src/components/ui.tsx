/** Minimal shadcn-style UI primitives — Button, Badge, Card, Progress, Sheet (drawer). */
import { createContext, useContext, useState, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "../lib/utils";

// ---------- Button ----------
type ButtonVariant = "default" | "ghost" | "secondary" | "outline" | "destructive";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({ variant = "default", size = "md", className, ...props }: ButtonProps) {
  const variants: Record<ButtonVariant, string> = {
    default: "bg-[var(--color-primary)] text-[var(--color-primary-foreground)] hover:opacity-90",
    ghost: "hover:bg-[var(--color-accent)] hover:text-[var(--color-accent-foreground)]",
    secondary: "bg-[var(--color-secondary)] text-[var(--color-secondary-foreground)] hover:opacity-90",
    outline: "border border-[var(--color-border)] bg-transparent hover:bg-[var(--color-accent)]",
    destructive: "bg-[var(--color-destructive)] text-[var(--color-destructive-foreground)] hover:opacity-90",
  };
  const sizes: Record<ButtonSize, string> = {
    sm: "h-7 px-2.5 text-xs rounded-md",
    md: "h-9 px-4 text-sm rounded-md",
    lg: "h-10 px-6 text-sm rounded-md",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

// ---------- Badge ----------
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline" | "secondary";
}

export function Badge({ variant = "default", className, ...props }: BadgeProps) {
  const variants = {
    default: "bg-[var(--color-primary)] text-[var(--color-primary-foreground)]",
    outline: "border border-[var(--color-border)] text-[var(--color-foreground)]",
    secondary: "bg-[var(--color-secondary)] text-[var(--color-secondary-foreground)]",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium leading-none",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

// ---------- Card ----------
export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-[var(--color-card-foreground)] shadow-sm",
        className
      )}
      {...props}
    />
  );
}

// ---------- Progress (10-segment bar per spec §9.1) ----------
interface ProgressProps {
  value: number; // 0-100
  className?: string;
  color?: string; // tailwind text-color class for filled segments
}

export function Progress({ value, className, color = "text-[var(--color-primary)]" }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const filledCount = Math.round(clamped / 10); // 0-10
  return (
    <span className={cn("inline-flex items-center", color, className)}>
      {Array.from({ length: 10 }).map((_, i) => (
        <span
          key={i}
          className={cn(
            "inline-block w-[6px] h-[10px] mr-[2px] rounded-[1px]",
            i < filledCount ? "bg-current" : "bg-[var(--color-muted)]"
          )}
        />
      ))}
    </span>
  );
}

// ---------- Sheet (right-side drawer) ----------
interface SheetContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const SheetContext = createContext<SheetContextValue | null>(null);

export function Sheet({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return <SheetContext.Provider value={{ open, setOpen }}>{children}</SheetContext.Provider>;
}

export function SheetTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const ctx = useContext(SheetContext);
  if (!ctx) throw new Error("SheetTrigger must be inside <Sheet>");
  const onClick = () => ctx.setOpen(true);
  if (asChild) {
    // simple clone — doesn't handle complex children
    return <span onClick={onClick}>{children}</span>;
  }
  return (
    <button onClick={onClick} className="contents">
      {children}
    </button>
  );
}

export function SheetContent({
  children,
  side = "right",
  title,
}: {
  children: ReactNode;
  side?: "right" | "left";
  title?: string;
}) {
  const ctx = useContext(SheetContext);
  if (!ctx) throw new Error("SheetContent must be inside <Sheet>");
  if (!ctx.open) return null;
  return (
    <div className="fixed inset-0 z-50 flex">
      {side === "right" && (
        <div
          className="flex-1 bg-black/30 backdrop-blur-sm"
          onClick={() => ctx.setOpen(false)}
        />
      )}
      <div
        className={cn(
          "w-full max-w-md bg-[var(--color-card)] border-[var(--color-border)] shadow-xl flex flex-col",
          side === "right" ? "border-l" : "border-r order-first"
        )}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
          <h3 className="text-sm font-semibold">{title}</h3>
          <button
            onClick={() => ctx.setOpen(false)}
            className="text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-auto px-5 py-4">{children}</div>
      </div>
      {side === "left" && (
        <div
          className="flex-1 bg-black/30 backdrop-blur-sm"
          onClick={() => ctx.setOpen(false)}
        />
      )}
    </div>
  );
}

// ---------- Input ----------
export const Input = ({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) => (
  <input
    className={cn(
      "h-9 w-full rounded-md border border-[var(--color-input)] bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-[var(--color-muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
      className
    )}
    {...props}
  />
);

// ---------- Textarea ----------
export const Textarea = ({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => (
  <textarea
    className={cn(
      "min-h-[80px] w-full rounded-md border border-[var(--color-input)] bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-[var(--color-muted-foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)]",
      className
    )}
    {...props}
  />
);

// ---------- Modal ----------
export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md p-6">
        <h2 className="text-base font-semibold mb-3">{title}</h2>
        <div className="text-sm text-[var(--color-muted-foreground)] mb-5">{children}</div>
        {footer && <div className="flex justify-end gap-2 mt-5">{footer}</div>}
      </Card>
    </div>
  );
}
