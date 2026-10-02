"use client";

import { AppShell } from "@/components/shell";
import { Button, TextArea } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Citation, CompareResult, DocumentItem } from "@/lib/types";
import { STATUS_LABEL } from "@/lib/types";
import { formatPercent } from "@/lib/utils";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";

const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((mod) => mod.PdfViewer), { ssr: false });

export default function ComparePage() {
  return (
    <AppShell>
      <Suspense fallback={<p className="text-sm text-slate-500">Opening comparison…</p>}>
        <CompareWorkspace />
      </Suspense>
    </AppShell>
  );
}

function CompareWorkspace() {
  const { token } = useAuth();
  const params = useSearchParams();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [question, setQuestion] = useState("What is the attendance requirement?");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [files, setFiles] = useState<Record<string, Blob>>({});
  const [focus, setFocus] = useState<Citation | null>(null);
  const [viewerPage, setViewerPage] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!token) return;
    client.documents(token).then((payload) => {
      setDocuments(payload.documents);
      const fromQuery = (params.get("docs") || "").split(",").filter(Boolean);
      setSelected(fromQuery.length >= 2 ? fromQuery : payload.documents.slice(0, 2).map((document) => document.id));
    });
  }, [params, token]);

  useEffect(() => {
    if (!token) return;
    selected.forEach((id) => {
      if (files[id]) return;
      client.file(token, id).then((blob) => setFiles((current) => ({ ...current, [id]: blob }))).catch(() => undefined);
    });
  }, [files, selected, token]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!token) return;
    if (selected.length < 2) {
      setError("Select at least two documents to compare.");
      return;
    }
    setPending(true);
    setError("");
    try {
      const comparison = await client.compare(token, { document_ids: selected, user_question: question });
      setResult(comparison);
      const first = comparison.documents[0]?.citations[0] || null;
      setFocus(first);
      if (first) setViewerPage({ [first.document_id]: first.page_number });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The comparison could not be completed.");
    } finally {
      setPending(false);
    }
  }

  function focusCitation(citation: Citation) {
    setFocus(citation);
    setViewerPage((current) => ({ ...current, [citation.document_id]: citation.page_number }));
  }

  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-iris">Compare documents</p>
      <h1 className="mt-1 font-display text-4xl text-navy">Side by side</h1>
      <form onSubmit={submit} className="mt-4 rounded-3xl border border-line bg-white p-4">
        <div className="flex flex-wrap gap-3">
          {documents.map((document) => (
            <label key={document.id} className="flex items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm">
              <input
                type="checkbox"
                checked={selected.includes(document.id)}
                onChange={() =>
                  setSelected((current) => (current.includes(document.id) ? current.filter((id) => id !== document.id) : [...current, document.id]))
                }
              />
              {document.title}
            </label>
          ))}
        </div>
        <TextArea className="mt-3" rows={2} value={question} onChange={(event) => setQuestion(event.target.value)} />
        <Button type="submit" className="mt-3" disabled={pending}>
          {pending ? "Comparing passages…" : "Compare"}
        </Button>
      </form>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {result ? (
        <div className="mt-5 space-y-4">
          <p className="text-sm font-semibold text-navy">
            {STATUS_LABEL[result.answer_status]} · {formatPercent(result.confidence)}
          </p>
          <p className="text-sm text-slate-600">{result.summary}</p>
          <div className={`grid gap-4 ${result.documents.length > 1 ? "lg:grid-cols-2" : ""}`}>
            {result.documents.map((column) => (
              <article key={column.document_id} className="rounded-3xl border border-line bg-white p-4">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">{column.category}</p>
                <h2 className="mt-1 font-display text-2xl text-navy">{column.title}</h2>
                <p className="mt-3 text-sm leading-6 text-slate-700">{column.summary}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {column.citations.map((citation) => (
                    <button key={citation.quoted_text} className="rounded-full border border-line px-3 py-1 text-xs font-semibold" onClick={() => {
                      setFocus(citation);
                      setViewerPage((current) => ({ ...current, [citation.document_id]: citation.page_number }));
                    }}>
                      p.{citation.page_number} · {citation.section}
                    </button>
                  ))}
                </div>
                <div className="mt-4 h-[460px]">
                  <PdfViewer
                    file={files[column.document_id] || null}
                    page={viewerPage[column.document_id] || (focus?.document_id === column.document_id ? focus.page_number : column.citations[0]?.page_number || 1)}
                    highlight={focus?.document_id === column.document_id ? focus.quoted_text : column.citations[0]?.quoted_text || ""}
                    onPageChange={(nextPage) => setViewerPage((current) => ({ ...current, [column.document_id]: nextPage }))}
                    fileName={column.document_name}
                  />
                </div>
              </article>
            ))}
          </div>
          <PointList title="Similarities" points={result.similarities} empty="No shared phrases were found in the retrieved passages." onCitation={focusCitation} />
          <PointList title="Differences" points={result.differences} empty="No differences were retrieved." onCitation={focusCitation} />
          <PointList title="Conflicting information" points={result.conflicts} empty="No conflicting passages were retrieved." onCitation={focusCitation} tone="red" />
        </div>
      ) : null}
    </div>
  );
}

function PointList({
  title,
  points,
  empty,
  onCitation,
  tone = "navy",
}: {
  title: string;
  points: { text: string; citations: Citation[] }[];
  empty: string;
  onCitation: (citation: Citation) => void;
  tone?: "navy" | "red";
}) {
  return (
    <section className={`rounded-3xl border p-4 ${tone === "red" ? "border-red-200 bg-red-50" : "border-line bg-white"}`}>
      <h2 className="font-semibold text-navy">{title}</h2>
      {points.length === 0 ? <p className="mt-2 text-sm text-slate-600">{empty}</p> : null}
      <ul className="mt-2 space-y-3">
        {points.map((point) => (
          <li key={point.text}>
            <p className="text-sm leading-6 text-ink">{point.text}</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {point.citations.map((citation) => (
                <button key={`${citation.document_name}-${citation.quoted_text}`} className="text-xs font-semibold text-iris" onClick={() => onCitation(citation)}>
                  {citation.document_name.replace(".pdf", "")} · p.{citation.page_number}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
