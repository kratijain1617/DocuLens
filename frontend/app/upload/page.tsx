"use client";

import { AppShell } from "@/components/shell";
import { Button, Select, TextInput } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CATEGORIES, type DocumentItem } from "@/lib/types";
import Link from "next/link";
import { useMemo, useState } from "react";

type Draft = { file: File; title: string; category: string; status?: DocumentItem; error?: string };

const STEPS = [
  "Uploading document",
  "Extracting text",
  "Detecting document type",
  "Splitting content into sections",
  "Creating embeddings",
  "Indexing document",
  "Ready for questions",
];

const STATUS_INDEX: Record<string, number> = {
  uploading: 0,
  extracting: 1,
  classifying: 2,
  splitting: 3,
  embedding: 4,
  indexing: 5,
  ready: 6,
};

export default function UploadPage() {
  return (
    <AppShell>
      <Upload />
    </AppShell>
  );
}

function Upload() {
  const { token } = useAuth();
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [dragging, setDragging] = useState(false);
  const [message, setMessage] = useState("");

  function addFiles(files: File[]) {
    const next = files.filter((file) => file.name.toLowerCase().endsWith(".pdf"));
    const rejected = files.length - next.length;
    const oversized = next.filter((file) => file.size > 20 * 1024 * 1024);
    const accepted = next.filter((file) => file.size <= 20 * 1024 * 1024);
    setDrafts((current) => [
      ...current,
      ...accepted.map((file) => ({ file, title: file.name.replace(/\.pdf$/i, ""), category: "Auto-detect" })),
    ]);
    const notes = [];
    if (rejected) notes.push("Only PDF files can be added.");
    if (oversized.length) notes.push("Files larger than 20 MB were skipped.");
    setMessage(notes.join(" "));
  }

  const active = useMemo(() => drafts.filter((draft) => draft.status), [drafts]);

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-iris">Upload</p>
      <h1 className="mt-1 font-display text-4xl text-navy">Add a PDF</h1>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Up to 5 documents per session, 20 MB each, and 200 pages per PDF. DocuLens reads the text layer. It does not run the file.
      </p>
      <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
        Do not upload unnecessary sensitive information, such as government ID numbers, full account numbers, or medical details. You can delete a document at any time.
      </p>
      <label
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          addFiles(Array.from(event.dataTransfer.files));
        }}
        className={`mt-5 block cursor-pointer rounded-3xl border-2 border-dashed px-6 py-12 text-center ${dragging ? "border-iris bg-white" : "border-line bg-white"}`}
      >
        <p className="font-semibold text-navy">Drag and drop PDF files</p>
        <p className="mt-1 text-sm text-slate-500">or click to browse. You can add more than one.</p>
        <input
          type="file"
          accept="application/pdf,.pdf"
          multiple
          className="sr-only"
          onChange={(event) => addFiles(Array.from(event.target.files || []))}
        />
      </label>
      {message ? <p className="mt-3 text-sm text-red-700">{message}</p> : null}
      <div className="mt-5 space-y-4">
        {drafts.map((draft, index) => (
          <article key={`${draft.file.name}-${index}`} className="rounded-3xl border border-line bg-white p-4">
            <p className="text-sm font-semibold text-navy">{draft.file.name}</p>
            <p className="text-xs text-slate-500">{(draft.file.size / 1024 / 1024).toFixed(1)} MB</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <label className="text-sm font-semibold text-navy">
                Title
                <TextInput className="mt-1 font-normal" value={draft.title} onChange={(event) => update(index, { title: event.target.value })} />
              </label>
              <label className="text-sm font-semibold text-navy">
                Category
                <Select className="mt-1 font-normal" value={draft.category} onChange={(event) => update(index, { category: event.target.value })}>
                  <option>Auto-detect</option>
                  {CATEGORIES.map((category) => (
                    <option key={category}>{category}</option>
                  ))}
                </Select>
              </label>
            </div>
            {draft.error ? <p className="mt-3 text-sm text-red-700">{draft.error}</p> : null}
            {draft.status ? <Steps status={draft.status.processing_status} error={draft.status.error_message} /> : null}
            {draft.status?.processing_status === "ready" ? (
              <Link href={`/ask?doc=${draft.status.id}`} className="mt-3 inline-block text-sm font-semibold text-iris">
                Ask a question about this document
              </Link>
            ) : null}
          </article>
        ))}
      </div>
      <Button className="mt-5" disabled={!drafts.length || drafts.every((draft) => draft.status)} onClick={() => void uploadAll()}>
        Upload {drafts.filter((draft) => !draft.status).length || ""} {drafts.filter((draft) => !draft.status).length === 1 ? "document" : "documents"}
      </Button>
      {active.length ? <p className="mt-3 text-xs text-slate-500">Classification suggests questions. It does not limit what you can ask.</p> : null}
    </div>
  );

  function update(index: number, patch: Partial<Draft>) {
    setDrafts((current) => current.map((draft, itemIndex) => (itemIndex === index ? { ...draft, ...patch } : draft)));
  }

  async function uploadAll() {
    if (!token) return;
    for (let index = 0; index < drafts.length; index += 1) {
      const draft = drafts[index];
      if (draft.status) continue;
      const form = new FormData();
      form.append("file", draft.file);
      form.append("title", draft.title);
      form.append("category", draft.category);
      try {
        let status = await client.upload(token, form);
        update(index, { status, error: undefined });
        for (let attempt = 0; attempt < 40 && status.processing_status !== "ready" && status.processing_status !== "error"; attempt += 1) {
          await new Promise((resolve) => setTimeout(resolve, 500));
          status = await client.document(token, status.id);
          update(index, { status });
        }
      } catch (err) {
        update(index, { error: err instanceof ApiError ? err.message : "The upload failed." });
      }
    }
  }
}

function Steps({ status, error }: { status: string; error?: string | null }) {
  const current = STATUS_INDEX[status] ?? 0;
  return (
    <ol className="mt-4 space-y-1">
      {STEPS.map((step, index) => (
        <li key={step} className={`text-sm ${index < current ? "text-emerald-700" : index === current ? "font-semibold text-navy" : "text-slate-400"}`}>
          {index < current ? "✓" : index === current ? "•" : "○"} {step}
        </li>
      ))}
      {error ? <li className="text-sm text-red-700">{error}</li> : null}
    </ol>
  );
}
