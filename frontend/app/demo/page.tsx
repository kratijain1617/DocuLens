"use client";

import { AnswerCard } from "@/components/answer-card";
import { Logo } from "@/components/logo";
import { Button, buttonClass } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AnswerRecord, CompareResult, DocumentItem, EvalSummary } from "@/lib/types";
import { formatPercent } from "@/lib/utils";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((mod) => mod.PdfViewer), { ssr: false });

const STEPS = [
  { id: "library", label: "Library" },
  { id: "deposit", label: "Cited answer" },
  { id: "missing", label: "Not found" },
  { id: "findings", label: "Research paper" },
  { id: "compare", label: "Compare" },
  { id: "evaluate", label: "Evaluation" },
];

export default function DemoPage() {
  const { setSession } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [error, setError] = useState("");
  const [deposit, setDeposit] = useState<AnswerRecord | null>(null);
  const [missing, setMissing] = useState<AnswerRecord | null>(null);
  const [findings, setFindings] = useState<AnswerRecord | null>(null);
  const [comparison, setComparison] = useState<CompareResult | null>(null);
  const [evaluation, setEvaluation] = useState<EvalSummary | null>(null);
  const [file, setFile] = useState<Blob | null>(null);
  const [page, setPage] = useState(1);
  const [highlight, setHighlight] = useState("");
  const [fileName, setFileName] = useState("");
  const loadedFile = useRef("");

  useEffect(() => {
    let cancelled = false;
    client
      .demo()
      .then(async (session) => {
        if (cancelled) return;
        setSession(session.token, session.user);
        setToken(session.token);
        const library = await client.documents(session.token);
        if (!cancelled) setDocuments(library.documents);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "The demo library could not be prepared."));
    return () => {
      cancelled = true;
    };
  }, [setSession]);

  useEffect(() => {
    if (!playing || !documents.length) return;
    const timer = window.setTimeout(() => setStep((current) => (current + 1) % STEPS.length), 8000);
    return () => window.clearTimeout(timer);
  }, [documents.length, playing, step]);

  useEffect(() => {
    if (!token || !documents.length) return;
    const rental = documents.find((document) => document.title.includes("Rental"));
    const paper = documents.find((document) => document.title === "Research Paper");
    const university = documents.find((document) => document.title.includes("University"));
    const handbook = documents.find((document) => document.title === "Employee Handbook");
    const current = STEPS[step].id;
    if ((current === "deposit" || current === "missing") && rental && loadedFile.current !== rental.file_name) {
      loadedFile.current = rental.file_name;
      client.file(token, rental.id).then((blob) => {
        setFile(blob);
        setFileName(rental.file_name);
      });
    }
    if (current === "findings" && paper && loadedFile.current !== paper.file_name) {
      loadedFile.current = paper.file_name;
      client.file(token, paper.id).then((blob) => {
        setFile(blob);
        setFileName(paper.file_name);
      });
    }
    if (current === "deposit" && rental && !deposit) {
      client
        .ask(token, { document_ids: [rental.id], user_question: "What is the security deposit?", conversation_history: [] })
        .then((result) => {
          setDeposit(result);
          const citation = result.citations[0];
          if (citation) {
            setPage(citation.page_number);
            setHighlight(citation.quoted_text);
          }
        });
    }
    if (current === "missing" && rental && !missing) {
      client
        .ask(token, {
          document_ids: [rental.id],
          user_question: "What happens if I do something that is not mentioned in the agreement?",
          conversation_history: [],
        })
        .then((result) => {
          setMissing(result);
          setHighlight("");
        });
    }
    if (current === "findings" && paper && !findings) {
      client
        .ask(token, { document_ids: [paper.id], user_question: "What were the main findings?", conversation_history: [] })
        .then((result) => {
          setFindings(result);
          const citation = result.citations[0];
          if (citation) {
            setPage(citation.page_number);
            setHighlight(citation.quoted_text);
          }
        });
    }
    if (current === "compare" && university && handbook && !comparison) {
      client
        .compare(token, {
          document_ids: [university.id, handbook.id],
          user_question: "What is the attendance requirement?",
        })
        .then(setComparison);
    }
    if (current === "evaluate" && !evaluation) {
      client.evaluate(token).then((payload) => setEvaluation(payload.summary));
    }
  }, [comparison, deposit, documents, evaluation, findings, missing, step, token]);

  const rental = documents.find((document) => document.title.includes("Rental"));
  const readingStep = STEPS[step].id === "deposit" || STEPS[step].id === "missing" || STEPS[step].id === "findings";
  const activeAnswer = STEPS[step].id === "deposit" ? deposit : STEPS[step].id === "missing" ? missing : STEPS[step].id === "findings" ? findings : null;

  return (
    <div className="min-h-screen bg-paper">
      <header className="flex items-center justify-between border-b border-line bg-white px-4 py-3">
        <Link href="/">
          <Logo />
        </Link>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setPlaying((value) => !value)}>
            {playing ? "Pause" : "Play"}
          </Button>
          <Link href="/library" className={buttonClass("ghost")}>
            Open the app
          </Link>
        </div>
      </header>
      <div className="mx-auto grid max-w-6xl gap-4 px-4 py-5 lg:grid-cols-[220px_minmax(0,1fr)]">
        <ol className="space-y-2">
          {STEPS.map((item, index) => (
            <li key={item.id}>
              <button
                onClick={() => {
                  setPlaying(false);
                  setStep(index);
                }}
                className={`w-full rounded-2xl px-3 py-2 text-left text-sm ${index === step ? "bg-navy text-white" : "bg-white text-navy"}`}
              >
                {index + 1}. {item.label}
              </button>
            </li>
          ))}
        </ol>
        <section className="space-y-4">
          {error ? <p className="rounded-2xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          {!documents.length && !error ? <p className="text-sm text-slate-500">Preparing five sample documents…</p> : null}
          {STEPS[step].id === "library" ? (
            <div>
              <h1 className="font-display text-4xl text-navy">Five documents, ready to question</h1>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {documents.map((document) => (
                  <article key={document.id} className="rounded-3xl border border-line bg-white p-4">
                    <h2 className="font-display text-2xl text-navy">{document.title}</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      {document.category} · {document.page_count} pages · {document.chunk_count} sections
                    </p>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {readingStep ? (
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
              <div>
                <p className="text-sm font-semibold text-slate-500">{STEPS[step].id === "findings" ? "Research Paper" : rental?.title}</p>
                <p className="mt-1 text-lg font-semibold text-navy">
                  {STEPS[step].id === "deposit"
                    ? "What is the security deposit?"
                    : STEPS[step].id === "missing"
                      ? "What happens if I do something that is not mentioned in the agreement?"
                      : "What were the main findings?"}
                </p>
                <div className="mt-3">
                  {activeAnswer ? (
                    <AnswerCard
                      result={activeAnswer}
                      activeQuote={highlight}
                      onCitation={(citation) => {
                        setPage(citation.page_number);
                        setHighlight(citation.quoted_text);
                      }}
                    />
                  ) : (
                    <p className="text-sm text-slate-500">Reading the cited pages…</p>
                  )}
                </div>
              </div>
              <PdfViewer file={file} page={page} highlight={highlight} onPageChange={setPage} fileName={fileName} />
            </div>
          ) : null}
          {STEPS[step].id === "compare" ? (
            <div>
              <h1 className="font-display text-4xl text-navy">Attendance, compared</h1>
              {!comparison ? <p className="mt-3 text-sm text-slate-500">Comparing attendance and on-site rules…</p> : null}
              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                {comparison?.documents.map((column) => (
                  <article key={column.document_id} className="rounded-3xl border border-line bg-white p-4">
                    <h2 className="font-display text-2xl text-navy">{column.title}</h2>
                    <p className="mt-3 text-sm leading-6">{column.summary}</p>
                    {column.citations[0] ? (
                      <p className="mt-3 text-xs font-semibold text-iris">
                        {column.document_name.replace(".pdf", "")} · page {column.citations[0].page_number} · {column.citations[0].section}
                      </p>
                    ) : null}
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {STEPS[step].id === "evaluate" ? (
            <div>
              <h1 className="font-display text-4xl text-navy">Evaluation dashboard</h1>
              {!evaluation ? <p className="mt-3 text-sm text-slate-500">Running the labeled questions…</p> : null}
              {evaluation ? (
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Stat label="Answer correctness" value={formatPercent(evaluation.answer_correctness)} />
                  <Stat label="Citation correctness" value={formatPercent(evaluation.citation_correctness)} />
                  <Stat label="Correct page rate" value={formatPercent(evaluation.correct_page_rate)} />
                  <Stat label="Grounding" value={formatPercent(evaluation.citation_grounding_rate)} />
                  <Stat label="Retrieval hit rate" value={formatPercent(evaluation.retrieval_hit_rate)} />
                  <Stat label="Unsupported answers" value={formatPercent(evaluation.unsupported_answer_rate)} />
                </div>
              ) : null}
              <Link href="/evaluate" className="mt-4 inline-block text-sm font-semibold text-iris">
                Open the full dashboard
              </Link>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-3xl border border-line bg-white p-4">
      <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-2 font-display text-3xl text-navy">{value}</p>
    </article>
  );
}
