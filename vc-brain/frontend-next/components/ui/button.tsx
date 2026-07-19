"use client";
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40",
  {
    variants: {
      variant: {
        default: "bg-accent text-white hover:bg-accent-hover",
        ghost: "hover:bg-elevated hover:text-text-primary",
        secondary: "bg-elevated text-text-primary hover:bg-modal",
        outline: "border border-border-strong bg-transparent hover:bg-elevated",
        destructive: "bg-error text-white hover:bg-error/90",
      },
      size: {
        sm: "h-7 px-2.5 text-xs rounded-md",
        md: "h-9 px-4 text-sm rounded-md",
        lg: "h-10 px-6 text-sm rounded-md",
      },
    },
    defaultVariants: { variant: "default", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
