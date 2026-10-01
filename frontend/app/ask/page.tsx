"use client";

import { AnswerCard } from "@/components/answer-card";
import { AppShell } from "@/components/shell";
import { Button, TextArea } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AnswerRecord, Citation, DocumentItem, DocumentSummary } from "@/lib/types";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";

const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((mod) => mod.PdfViewer), { ssr: false });

export default function AskPage() {
  return (
    <AppShell>
      <Suspense fallback={<p className="text-sm text-slate-500">Opening the workspace…</p>}>
        <Workspace />
      </Suspense>
    </AppShell>
  );
}

function Workspace() {
  const { token } = useAuth();
  const params = useSearchParams();
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activeId, setActiveId] = useState(params.get("doc") || "");
  const [checked, setChecked] = useState<string[]>(params.get("doc") ? [params.get("doc") as string] : []);
  const [filter, setFilter] = useState("All");
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<AnswerRecord[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState<Blob | null>(null);
  const [page, setPage] = useState(1);
  const [highlight, setHighlight] = useState("");
  const [summary, setSummary] = useState<DocumentSummary | null>(null);
  const [pane, setPane] = useState<"docs" | "answer" | "source">("answer");

  useEffect(() => {
    if (!token) return;
    client.documents(token).then((result) => {
      setDocuments(result.documents);
      const requested = params.get("doc");
      const initial = result.documents.find((document) => document.id === requested) || result.documents.find((document) => document.processing_status === "ready");
      if (initial) {
        setActiveId(initial.id);
        setChecked((current) => (current.length ? current : [initial.id]));
      }
    });
  }, [params, token]);

  useEffect(() => {
    if (!token || !activeId) return;
    setSummary(null);
    client.history(token, activeId).then((result) => setHistory(result.history)).catch(() => setHistory([]));
    client.file(token, activeId).then(setFile).catch(() => setFile(null));
  }, [activeId, token]);

  const active = documents.find((document) => document.id === activeId);
  const categories = useMemo(() => ["All", ...Array.from(new Set(documents.map((document) => document.category)))], [documents]);
  const visible = documents.filter((document) => filter === "All" || document.category === filter);
  const latest = history[history.length - 1];

  async function ask(text: string, idsOverride?: string[]) {
    if (!token || !text.trim()) return;
    const ids = idsOverride || (checked.length ? checked : activeId ? [activeId] : []);
    if (!ids.length) {
      setError("Select a document before asking.");
      return;
    }
    setPending(true);
    setError("");
    setPane("answer");
    try {
      const result = await client.ask(token, {
        document_ids: ids,
        user_question: text.trim(),
        conversation_history: history.slice(-6).flatMap((item) => [
          { role: "user", content: item.question },
          { role: "assistant", content: item.answer },
        ]),
        selected_page: page,
        document_category: active?.category,
      });
      setHistory((current) => [...current, result]);
      setQuestion("");
      openCitation(result.citations[0]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The question could not be answered.");
    } finally {
      setPending(false);
    }
  }

  function openCitation(citation?: Citation) {
    if (!citation) return;
    setActiveId(citation.document_id);
    setPage(citation.page_number);
    setHighlight(citation.quoted_text);
    setPane("source");
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  return (
    <div>
      <div className="mb-4 flex gap-2 lg:hidden">
        {(["docs", "answer", "source"] as const).map((item) => (
          <button key={item} onClick={() => setPane(item)} className={`rounded-full px-3 py-1.5 text-sm font-semibold ${pane === item ? "bg-navy text-white" : "bg-white text-navy"}`}>
            {item === "docs" ? "Documents" : item === "answer" ? "Answer" : "Source"}
          </button>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)_380px]">
        <aside className={`${pane === "docs" ? "block" : "hidden"} rounded-3xl border border-line bg-white p-4 lg:block`}>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-navy">Documents</h2>
            <Link href={checked.length >= 2 ? `/compare?docs=${checked.join(",")}` : "/compare"} className="text-xs font-semibold text-iris">
              Compare
            </Link>
          </div>
          <select value={filter} onChange={(event) => setFilter(event.target.value)} className="mt-3 w-full rounded-xl border border-line px-2 py-2 text-sm" aria-label="Filter by category">
            {categories.map((category) => (
              <option key={category}>{category}</option>
            ))}
          </select>
          <ul className="mt-3 space-y-2">
            {visible.map((document) => (
              <li key={document.id} className={`rounded-2xl border px-3 py-2 ${document.id === activeId ? "border-iris bg-indigo-50" : "border-line"}`}>
                <label className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={checked.includes(document.id)}
                    onChange={() => setChecked((current) => (current.includes(document.id) ? current.filter((id) => id !== document.id) : [...current, document.id]))}
                    aria-label={`Include ${document.title}`}
                  />
                  <button
                    className="text-left"
                    onClick={() => {
                      setActiveId(document.id);
                      setPage(1);
                      setHighlight("");
                      router.replace(`/ask?doc=${document.id}`);
                    }}
                  >
                    <span className="block text-sm font-semibold text-navy">{document.title}</span>
                    <span className="block text-xs text-slate-500">{document.category}</span>
                  </button>
                </label>
              </li>
            ))}
          </ul>
        </aside>

        <section className={`${pane === "answer" ? "block" : "hidden"} space-y-4 lg:block`}>
          <form onSubmit={submit} className="rounded-3xl border border-line bg-white p-4 shadow-card">
            <label className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500" htmlFor="question">
              Ask Lens
            </label>
            <TextArea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask in ordinary language. The answer will quote the page."
              rows={3}
              className="mt-2"
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void ask(question);
                }
              }}
            />
            <div className="mt-3 flex flex-wrap gap-2">
              <Button type="submit" disabled={pending}>{pending ? "Reading the pages…" : "Ask"}</Button>
              <Button
                type="button"
                variant="secondary"
                disabled={!active || active.processing_status !== "ready"}
                onClick={async () => {
                  if (!token || !active) return;
                  setPending(true);
                  try {
                    setSummary(await client.summarize(token, active.id));
                  } catch (err) {
                    setError(err instanceof ApiError ? err.message : "The summary could not be created.");
                  } finally {
                    setPending(false);
                  }
                }}
              >
                Summarize document
              </Button>
            </div>
            {active ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {active.suggested_questions.map((suggestion) => (
                  <button key={suggestion} type="button" onClick={() => void ask(suggestion)} className="rounded-full bg-paper px-3 py-1 text-left text-xs font-medium text-navy">
                    {suggestion}
                  </button>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-500">Upload a document or open the demo library to start.</p>
            )}
            <p className="mt-2 text-xs text-slate-500">Suggestions follow the document type. You can ask anything else.</p>
          </form>
          {error ? <p className="rounded-2xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          {summary ? <SummaryCard summary={summary} onCitation={openCitation} /> : null}
          {latest ? (
            <AnswerCard result={latest} onCitation={openCitation} onFollowUp={(value) => void ask(value)} activeQuote={highlight} />
          ) : null}
          {latest?.answer_status === "not_found" ? (
            <div className="rounded-3xl border border-line bg-white p-4">
              <p className="text-sm font-semibold text-navy">Search another document</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {documents
                  .filter((document) => document.id !== activeId)
                  .map((document) => (
                    <Button
                      key={document.id}
                      variant="secondary"
                      onClick={() => {
                        setChecked([document.id]);
                        setActiveId(document.id);
                        void ask(latest.question, [document.id]);
                      }}
                    >
                      {document.title}
                    </Button>
                  ))}
              </div>
            </div>
          ) : null}
          {history.length > 1 ? (
            <div className="space-y-2">
              <h2 className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Earlier questions</h2>
              {history.slice(0, -1).map((item) => (
                <button key={item.id || item.question} onClick={() => openCitation(item.citations[0])} className="block w-full rounded-2xl border border-line bg-white px-4 py-3 text-left">
                  <span className="block text-sm font-semibold text-navy">{item.question}</span>
                  <span className="mt-1 block line-clamp-2 text-sm text-slate-600">{item.answer}</span>
                </button>
              ))}
            </div>
          ) : null}
        </section>

        <div className={`${pane === "source" ? "block" : "hidden"} lg:block`}>
          <PdfViewer
            file={file}
            page={page}
            pageCount={active?.page_count}
            highlight={highlight}
            onPageChange={setPage}
            fileName={active?.file_name}
            onDownload={() => {
              if (!file || !active) return;
              const url = URL.createObjectURL(file);
              const anchor = document.createElement("a");
              anchor.href = url;
              anchor.download = active.file_name;
              anchor.click();
              URL.revokeObjectURL(url);
            }}
          />
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ summary, onCitation }: { summary: DocumentSummary; onCitation: (citation: Citation) => void }) {
  const groups = [
    ["Important dates", summary.important_dates],
    ["Important numbers", summary.important_numbers],
    ["Required actions", summary.required_actions],
    ["Definitions", summary.definitions],
    ["Risks or warnings", summary.risks_or_warnings],
  ] as const;
  return (
    <section className="rounded-3xl border border-line bg-white p-5">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-iris">Document summary</p>
      <h2 className="mt-2 font-display text-2xl text-navy">{summary.one_sentence}</h2>
      <p className="mt-3 text-sm leading-6 text-slate-700">{summary.detailed}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {summary.topics.map((topic) => (
          <span key={topic} className="rounded-full bg-paper px-3 py-1 text-xs font-medium text-navy">
            {topic}
          </span>
        ))}
      </div>
      {groups.map(([label, points]) => (
        <div key={label} className="mt-4">
          <h3 className="text-sm font-semibold text-navy">{label}</h3>
          {points.length === 0 ? <p className="text-sm text-slate-500">None found in the document.</p> : null}
          <ul className="mt-1 space-y-2">
            {points.map((point) => (
              <li key={point.text}>
                <button className="text-left text-sm leading-6 text-slate-700" onClick={() => onCitation(point.citation)}>
                  {point.text}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <div className="mt-4">
        <h3 className="text-sm font-semibold text-navy">Missing information</h3>
        {summary.missing_information.length === 0 ? (
          <p className="text-sm text-slate-500">The usual topics for this document type all appear at least once.</p>
        ) : (
          <p className="text-sm text-slate-700">{summary.missing_information.join(", ")}</p>
        )}
      </div>
    </section>
  );
}
