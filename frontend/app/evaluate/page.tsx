"use client";

import { AppShell } from "@/components/shell";
import { Button } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { EvalItemResult, EvalSummary } from "@/lib/types";
import { formatPercent } from "@/lib/utils";
import { Suspense, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function EvaluatePage() {
  return (
    <AppShell>
      <Suspense fallback={<p className="text-sm text-slate-500">Opening evaluation…</p>}>
        <Evaluation />
      </Suspense>
    </AppShell>
  );
}

function Evaluation() {
  const { token } = useAuth();
  const [dataset, setDataset] = useState<EvalItemResult[]>([]);
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [results, setResults] = useState<EvalItemResult[]>([]);
  const [filter, setFilter] = useState<"all" | "correct" | "incorrect">("all");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    client.dataset(token).then((payload) => setDataset(payload.items)).catch(() => undefined);
  }, [token]);

  const rows = results.length ? results : dataset;
  const visible = rows.filter((item) => {
    if (!results.length || filter === "all") return true;
    const correct = Boolean(item.answer_correct && item.citation_correct);
    return filter === "correct" ? correct : !correct;
  });
  const chart = summary
    ? [
        { name: "Answer", value: Math.round(summary.answer_correctness * 100) },
        { name: "Citation", value: Math.round(summary.citation_correctness * 100) },
        { name: "Page", value: Math.round(summary.correct_page_rate * 100) },
        { name: "Grounding", value: Math.round(summary.citation_grounding_rate * 100) },
        { name: "Retrieval", value: Math.round(summary.retrieval_hit_rate * 100) },
        { name: "Unsupported", value: Math.round(summary.unsupported_answer_rate * 100) },
      ]
    : [];

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-iris">Evaluation</p>
          <h1 className="mt-1 font-display text-4xl text-navy">Labeled questions</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            {dataset.length || 20}+ questions across rental agreements, university policy, a technical manual, a research paper, and an employee handbook.
          </p>
        </div>
        <Button
          disabled={pending}
          onClick={async () => {
            if (!token) return;
            setPending(true);
            setError("");
            try {
              const payload = await client.evaluate(token);
              setSummary(payload.summary);
              setResults(payload.results);
            } catch (err) {
              setError(err instanceof ApiError ? err.message : "The evaluation could not be completed.");
            } finally {
              setPending(false);
            }
          }}
        >
          {pending ? "Running evaluation…" : "Run Evaluation"}
        </Button>
      </div>
      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
      {summary ? (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Answer correctness" value={formatPercent(summary.answer_correctness)} />
            <Metric label="Citation correctness" value={formatPercent(summary.citation_correctness)} />
            <Metric label="Correct page rate" value={formatPercent(summary.correct_page_rate)} />
            <Metric label="Citation grounding" value={formatPercent(summary.citation_grounding_rate)} />
            <Metric label="Retrieval hit rate" value={formatPercent(summary.retrieval_hit_rate)} />
            <Metric label="Unsupported answers" value={formatPercent(summary.unsupported_answer_rate)} />
            <Metric label="Average response" value={`${summary.average_response_time_ms} ms`} />
            <Metric label="Questions" value={String(summary.total)} />
          </div>
          <div className="mt-5 h-72 rounded-3xl border border-line bg-white p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <CartesianGrid stroke="#E3E8EF" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#122033", fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#64748B", fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#1A3A68" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : null}
      <div className="mt-5 flex gap-2">
        {(["all", "correct", "incorrect"] as const).map((item) => (
          <button key={item} onClick={() => setFilter(item)} className={`rounded-full px-3 py-1 text-sm font-semibold ${filter === item ? "bg-navy text-white" : "bg-white text-navy"}`}>
            {item}
          </button>
        ))}
      </div>
      <div className="mt-4 overflow-x-auto rounded-3xl border border-line bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-line text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Question</th>
              <th className="px-4 py-3">Expected</th>
              <th className="px-4 py-3">Document</th>
              <th className="px-4 py-3">Page</th>
              <th className="px-4 py-3">Result</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((item) => {
              const correct = Boolean(item.answer_correct && item.citation_correct);
              return (
                <tr key={item.question} className="border-b border-line align-top">
                  <td className="px-4 py-3 font-medium text-navy">{item.question}</td>
                  <td className="max-w-xs px-4 py-3 text-slate-600">{item.expected_answer}</td>
                  <td className="px-4 py-3">{item.expected_document.replace(".pdf", "")}</td>
                  <td className="px-4 py-3">{item.expected_page ?? "—"}</td>
                  <td className="px-4 py-3">
                    {results.length ? (
                      <span className={correct ? "font-semibold text-emerald-700" : "font-semibold text-red-700"}>{correct ? "Correct" : "Incorrect"}</span>
                    ) : (
                      "Not run"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {results.length ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <Examples title="Correct examples" items={results.filter((item) => item.answer_correct && item.citation_correct).slice(0, 2)} />
          <Examples title="Incorrect examples" items={results.filter((item) => !(item.answer_correct && item.citation_correct)).slice(0, 2)} />
        </div>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-3xl border border-line bg-white p-4">
      <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-2 font-display text-3xl text-navy">{value}</p>
    </article>
  );
}

function Examples({ title, items }: { title: string; items: EvalItemResult[] }) {
  return (
    <section className="rounded-3xl border border-line bg-white p-4">
      <h2 className="font-semibold text-navy">{title}</h2>
      {items.length === 0 ? <p className="mt-2 text-sm text-slate-500">None in this run.</p> : null}
      {items.map((item) => (
        <div key={item.question} className="mt-3 border-t border-line pt-3">
          <p className="text-sm font-semibold text-navy">{item.question}</p>
          <p className="mt-1 text-sm text-slate-600">{item.answer}</p>
        </div>
      ))}
    </section>
  );
}
