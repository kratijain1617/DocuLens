import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

const VARIANTS = {
  primary: "bg-navy text-white hover:bg-navy-mid",
  secondary: "border border-line bg-white text-navy hover:border-navy/30",
  ghost: "text-navy hover:bg-white",
  danger: "border border-red-200 bg-white text-red-700 hover:bg-red-50",
};

export function buttonClass(variant: keyof typeof VARIANTS = "primary", className?: string) {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50",
    VARIANTS[variant],
    className,
  );
}

export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: keyof typeof VARIANTS }) {
  return <button type="button" className={buttonClass(variant, className)} {...props} />;
}

export function TextInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn("w-full rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none", className)}
      {...props}
    />
  );
}

export function TextArea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn("w-full rounded-2xl border border-line bg-white px-3 py-3 text-sm text-ink outline-none", className)}
      {...props}
    />
  );
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn("w-full rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none", className)}
      {...props}
    />
  );
}
