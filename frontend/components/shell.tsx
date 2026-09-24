"use client";

import { Logo } from "@/components/logo";
import { Disclaimer } from "@/components/disclaimer";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

const LINKS = [
  { href: "/library", label: "Library" },
  { href: "/upload", label: "Upload" },
  { href: "/ask", label: "Ask" },
  { href: "/compare", label: "Compare" },
  { href: "/evaluate", label: "Evaluation" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, ready, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, router, user]);

  if (!ready || !user) {
    return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Opening your library…</div>;
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3">
          <Link href="/library" aria-label="DocuLens library">
            <Logo />
          </Link>
          <nav className="flex flex-1 gap-1 overflow-x-auto">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-full px-3 py-1.5 text-sm font-medium text-slate-600",
                  pathname.startsWith(link.href) && "bg-navy text-white",
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold text-navy">{user.name}</p>
            <p className="text-xs text-slate-500">{user.is_demo ? "Demo session" : user.email}</p>
          </div>
          <button
            className="rounded-full px-3 py-1.5 text-sm font-semibold text-navy hover:bg-paper"
            onClick={async () => {
              await logout();
              router.push("/");
            }}
          >
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      <footer className="mx-auto max-w-7xl px-4 pb-8">
        <Disclaimer />
      </footer>
    </div>
  );
}
