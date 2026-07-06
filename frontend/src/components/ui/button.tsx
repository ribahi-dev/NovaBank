// Button — variants cva (convention shadcn/ui).
import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-all outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] disabled:opacity-50 disabled:pointer-events-none cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-brand-gradient text-primary-foreground shadow-sm hover:brightness-105 active:scale-[0.98]",
        secondary:
          "bg-card text-foreground border border-border hover:border-primary hover:text-primary",
        ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
        destructive: "bg-danger text-white hover:brightness-110",
        outline: "border border-primary text-primary hover:bg-primary-soft",
      },
      size: {
        default: "h-10 px-5",
        sm: "h-8 px-3 text-[13px]",
        lg: "h-11 px-7",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
);
Button.displayName = "Button";
