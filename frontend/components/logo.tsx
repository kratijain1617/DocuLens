import { cn } from "@/lib/utils";

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
        <rect x="2" y="4" width="16" height="22" rx="2.5" fill="#0E1C36" />
        <rect x="5.5" y="9" width="9" height="1.6" rx="0.8" fill="#D5DEEE" />
        <rect x="5.5" y="13" width="7" height="1.6" rx="0.8" fill="#D5DEEE" />
        <rect x="5.5" y="17" width="8" height="1.6" rx="0.8" fill="#D5DEEE" />
        <circle cx="22.5" cy="20.5" r="7.2" fill="#5146C8" />
        <circle cx="22.5" cy="20.5" r="3" fill="#F8F7FF" />
      </svg>
      {compact ? null : <span className="font-display text-[1.35rem] leading-none tracking-tight text-navy">DocuLens</span>}
    </span>
  );
}
