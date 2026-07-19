"use client";
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;
export const SheetClose = DialogPrimitive.Close;

export function SheetContent({
  children,
  side = "right",
  title,
}: {
  children: React.ReactNode;
  side?: "right" | "left";
  title?: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out" />
      <DialogPrimitive.Content
        className={cn(
          "fixed z-50 top-0 bottom-0 w-full max-w-md bg-modal border-border shadow-xl flex flex-col",
          side === "right" ? "right-0 border-l" : "left-0 border-r"
        )}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <DialogPrimitive.Title className="text-sm font-bold text-text-primary">
            {title}
          </DialogPrimitive.Title>
          <DialogPrimitive.Close className="text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </DialogPrimitive.Close>
        </div>
        <div className="flex-1 overflow-auto px-5 py-4">{children}</div>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

// Modal (centered)
export function Modal({
  open,
  onOpenChange,
  title,
  children,
  footer,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
        <DialogPrimitive.Content className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-modal border border-border-strong rounded-lg shadow-xl p-6">
          <DialogPrimitive.Title className="text-base font-bold mb-3 text-text-primary">
            {title}
          </DialogPrimitive.Title>
          <div className="text-sm text-text-secondary mb-5">{children}</div>
          {footer && <div className="flex justify-end gap-2 mt-5">{footer}</div>}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
