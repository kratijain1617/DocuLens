import { DISCLAIMER } from "@/lib/types";

export function Disclaimer({ className = "" }: { className?: string }) {
  return <p className={`text-xs leading-5 text-slate-500 ${className}`}>{DISCLAIMER}</p>;
}
