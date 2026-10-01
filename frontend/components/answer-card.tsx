"use client";

import { Button } from "@/components/ui";
import type { AnswerRecord, AnswerStatus, Citation } from "@/lib/types";
import { STATUS_LABEL } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

const TONE: Record<AnswerStatus, string> = {
  supported: "border-emerald-200 bg-emerald-50",
  partially_supported: "border-amber-200 bg-amber-50",
  conflicting_information: "border-red-200 bg-red-50",
  not_found: "border-amber-300 bg-amber-50",
};

const LABEL: Record<AnswerStatus, string> = {
  supported: "text-emerald-800",
  partially_supported: "text-amber-800",
  conflicting_information: "text-red-800",
  not_found: "text-amber-900",
};

export function AnswerCard({
  result,
  onCitation,
  onFollowUp,
  activeQuote,
}: {
  result: AnswerRecord;
  onCitation?: (citation: Citation) => void;
  onFollowUp?: (question: string) => void;
  activeQuote?: string;
}) {
  const weak = result.answer_status !== "supported" || result.confidence < 0.55;
  return (
    <article className={`rounded-3xl border p-5 shadow-card ${TONE[result.answer_status]}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className={`text-xs font-bold uppercase tracking-[0.16em] ${LABEL[result.answer_status]}`}>
          Lens · {STATUS_LABEL[result.answer_status]}
        </p>
        <p className="text-sm font-semibold text-navy">Confidence {formatPercent(result.confidence)}</p>
      </div>
      <h2 className="mt-3 font-display text-2xl leading-snug text-navy">{result.answer}</h2>
      {result.explanation ? <p className="mt-3 text-sm leading-6 text-slate-700">{result.explanation}</p> : null}
      {weak ? (
        <p className="mt-3 rounded-2xl border border-amber-300 bg-white/80 px-3 py-2 text-sm text-amber-900">
          {result.answer_status === "conflicting_information"
            ? "These passages disagree. DocuLens is showing both sources rather than choosing one."
            : "Evidence is limited. Check the cited page before relying on this answer."}
        </p>
      ) : null}
      {result.important_conditions.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">Conditions and exceptions</h3>
          <ul className="mt-2 space-y-2">
            {result.important_conditions.map((condition) => (
              <li key={condition} className="rounded-2xl bg-white/80 px-3 py-2 text-sm leading-6 text-ink">
                {condition}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {result.citations.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {result.citations.map((citation) => (
            <button
              key={`${citation.document_id}-${citation.page_number}-${citation.quoted_text}`}
              onClick={() => onCitation?.(citation)}
              className={`max-w-full rounded-full border bg-white px-3 py-1.5 text-left text-sm ${
                activeQuote === citation.quoted_text ? "border-iris text-navy" : "border-line text-slate-700"
              }`}
            >
              <span className="font-semibold">{citation.document_name.replace(".pdf", "")}</span>
              <span>
                {" "}
                · page {citation.page_number} · {citation.section}
              </span>
            </button>
          ))}
        </div>
      ) : null}
      {result.citations[0] ? (
        <blockquote className="mt-4 border-l-4 border-iris bg-white/75 px-4 py-3 text-sm leading-6 text-ink">
          “{result.citations.find((citation) => citation.quoted_text === activeQuote)?.quoted_text || result.citations[0].quoted_text}”
        </blockquote>
      ) : null}
      {result.related_sections.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
            {result.answer_status === "not_found" ? "Sections searched" : "Related sections"}
          </h3>
          <ul className="mt-2 flex flex-wrap gap-2">
            {result.related_sections.map((section) => (
              <li key={`${section.document_name}-${section.page_number}-${section.section}`} className="rounded-full bg-white px-3 py-1 text-xs text-slate-600">
                {section.section} · p.{section.page_number}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {result.follow_up_questions.length > 0 && onFollowUp ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {result.follow_up_questions.map((question) => (
            <Button key={question} variant="secondary" onClick={() => onFollowUp(question)}>
              {question}
            </Button>
          ))}
        </div>
      ) : null}
    </article>
  );
}
