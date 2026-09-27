"use client";

import { Disclaimer } from "@/components/disclaimer";
import { Logo } from "@/components/logo";
import { buttonClass } from "@/components/ui";
import { BookOpen, Building2, FileSearch, Files, GraduationCap, Landmark, Scale, Wrench } from "lucide-react";
import Link from "next/link";

const FEATURES = [
  {
    title: "Ask naturally",
    body: "Ask questions in normal language instead of searching manually.",
    icon: FileSearch,
  },
  {
    title: "See the evidence",
    body: "Every answer includes clickable citations and highlighted source passages.",
    icon: BookOpen,
  },
  {
    title: "Compare documents",
    body: "Find differences, conflicts, and missing information across multiple documents.",
    icon: Files,
  },
];

const CATEGORIES = [
  { title: "Research papers", icon: BookOpen },
  { title: "University documents", icon: GraduationCap },
  { title: "Legal and rental documents", icon: Scale },
  { title: "Technical manuals", icon: Wrench },
  { title: "Business reports", icon: Building2 },
  { title: "Government documents", icon: Landmark },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Logo />
        <nav className="flex items-center gap-2">
          <Link href="/login" className="rounded-full px-3 py-2 text-sm font-semibold text-navy">
            Log in
          </Link>
          <Link href="/signup" className="hidden rounded-full px-3 py-2 text-sm font-semibold text-navy sm:inline">
            Sign up
          </Link>
          <Link href="/demo" className="rounded-full bg-navy px-4 py-2 text-sm font-semibold text-white">
            Try Demo
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-16">
        <section className="grid items-center gap-10 py-8 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-iris">Ask questions. See the evidence.</p>
            <h1 className="mt-3 max-w-xl font-display text-5xl leading-[1.05] text-navy sm:text-6xl">Understand any document in seconds.</h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
              Upload a PDF, ask a question, and get an evidence-based answer with exact page citations.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/upload" className={buttonClass("primary", "px-5 py-3")}>
                Upload a Document
              </Link>
              <Link href="/demo" className={buttonClass("secondary", "px-5 py-3")}>
                Try Demo
              </Link>
            </div>
            <p className="mt-4 text-sm text-slate-500">No account needed for the demo. It runs without an API key.</p>
          </div>
          <Preview />
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="rounded-3xl border border-line bg-white p-5 shadow-card">
              <feature.icon className="text-iris" size={22} />
              <h2 className="mt-4 font-display text-2xl text-navy">{feature.title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{feature.body}</p>
            </article>
          ))}
        </section>

        <section className="mt-12">
          <h2 className="font-display text-3xl text-navy">Built for the documents people actually read</h2>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {CATEGORIES.map((category) => (
              <div key={category.title} className="flex items-center gap-3 rounded-2xl border border-line bg-white px-4 py-4">
                <category.icon size={18} className="text-navy" />
                <p className="font-semibold text-navy">{category.title}</p>
              </div>
            ))}
          </div>
        </section>

        <Disclaimer className="mt-12 max-w-3xl" />
      </main>
    </div>
  );
}

function Preview() {
  return (
    <div className="rounded-[28px] border border-line bg-white p-3 shadow-card">
      <div className="grid gap-3 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-2xl bg-paper p-4">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Question</p>
          <p className="mt-2 text-sm font-semibold text-navy">What is the security deposit?</p>
          <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-800">Supported · 94%</p>
            <p className="mt-2 font-display text-2xl leading-snug text-navy">The security deposit shall be equal to one month&apos;s rent.</p>
            <button className="mt-3 rounded-full border border-emerald-300 bg-white px-3 py-1 text-xs font-semibold text-navy">
              Apartment Rental Agreement · page 3 · Security Deposit
            </button>
          </div>
        </div>
        <div className="rounded-2xl border border-line bg-slate-50 p-4">
          <div className="mb-3 flex items-center justify-between text-xs text-slate-500">
            <span>Apartment Rental Agreement.pdf</span>
            <span>Page 3 of 8</span>
          </div>
          <div className="rounded-xl bg-white p-4 shadow-sm">
            <div className="h-2 w-24 rounded bg-navy" />
            <p className="mt-4 text-xs font-bold uppercase tracking-wide text-iris">Security Deposit</p>
            <p className="mt-3 text-sm leading-6 text-slate-700">
              The security deposit shall be equal to <mark className="rounded bg-yellow-300 px-1">one month&apos;s rent</mark>.
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-400">The landlord may apply the deposit to unpaid rent or damage beyond ordinary wear.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
