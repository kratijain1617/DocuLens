"use client";

import { AppShell } from "@/components/shell";
import { Button, TextInput, buttonClass } from "@/components/ui";
import { ApiError, client } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DocumentItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

export default function LibraryPage() {
  return (
    <AppShell>
      <Library />
    </AppShell>
  );
}

function Library() {
  const { token } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [filter, setFilter] = useState("All");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [title, setTitle] = useState("");

  async function load() {
    if (!token) return;
    const result = await client.documents(token);
    setDocuments(result.documents);
    setCategories(result.categories);
  }

  useEffect(() => {
    if (!token) return;
    load().catch((err) => setError(err instanceof ApiError ? err.message : "The library could not be loaded."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const visible = useMemo(
    () =>
      documents.filter((document) => {
        const categoryOk = filter === "All" || document.category === filter;
        const queryOk = document.title.toLowerCase().includes(query.toLowerCase()) || document.file_name.toLowerCase().includes(query.toLowerCase());
        return categoryOk && queryOk;
      }),
    [documents, filter, query],
  );

  function toggle(id: string) {
    setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-iris">Library</p>
          <h1 className="mt-1 font-display text-4xl text-navy">Your documents</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/upload" className={buttonClass("primary")}>
            Upload
          </Link>
          <Link href={selected.length >= 2 ? `/compare?docs=${selected.join(",")}` : "/library"} className={buttonClass("secondary", selected.length < 2 ? "pointer-events-none opacity-50" : "")} aria-disabled={selected.length < 2}>
            Compare documents
          </Link>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <TextInput value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search titles" className="max-w-xs" />
        <select value={filter} onChange={(event) => setFilter(event.target.value)} className="rounded-xl border border-line bg-white px-3 py-2 text-sm">
          <option>All</option>
          {categories.map((category) => (
            <option key={category}>{category}</option>
          ))}
        </select>
      </div>
      {error ? <p className="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {visible.length === 0 ? (
        <div className="mt-8 rounded-3xl border border-dashed border-line bg-white p-8 text-center">
          <p className="font-display text-2xl text-navy">No documents yet</p>
          <p className="mt-2 text-sm text-slate-600">Upload a PDF or try the demo library of five sample documents.</p>
          <div className="mt-4 flex justify-center gap-2">
            <Link href="/upload" className={buttonClass("primary")}>
              Upload a Document
            </Link>
            <Link href="/demo" className={buttonClass("secondary")}>
              Try Demo
            </Link>
          </div>
        </div>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {visible.map((document) => (
            <article key={document.id} className="rounded-3xl border border-line bg-white p-5 shadow-card">
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selected.includes(document.id)}
                  onChange={() => toggle(document.id)}
                  aria-label={`Select ${document.title}`}
                  className="mt-1"
                />
                <div className="min-w-0 flex-1">
                  {editing === document.id ? (
                    <form
                      className="flex gap-2"
                      onSubmit={async (event) => {
                        event.preventDefault();
                        if (!token) return;
                        const updated = await client.rename(token, document.id, title);
                        setDocuments((current) => current.map((item) => (item.id === updated.id ? updated : item)));
                        setEditing(null);
                      }}
                    >
                      <TextInput value={title} onChange={(event) => setTitle(event.target.value)} />
                      <Button type="submit">Save</Button>
                    </form>
                  ) : (
                    <h2 className="font-display text-2xl text-navy">{document.title}</h2>
                  )}
                  <p className="mt-1 text-sm text-slate-500">{document.file_name}</p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                    <span className="rounded-full bg-paper px-2 py-1">{document.category}</span>
                    <span className="rounded-full bg-paper px-2 py-1">{document.page_count} pages</span>
                    <span className="rounded-full bg-paper px-2 py-1">{document.chunk_count} chunks</span>
                    <span className="rounded-full bg-paper px-2 py-1">{document.question_count} questions</span>
                    <span className="rounded-full bg-paper px-2 py-1">{formatDate(document.created_at)}</span>
                    <Status status={document.processing_status} />
                  </div>
                  {document.error_message ? <p className="mt-3 text-sm text-red-700">{document.error_message}</p> : null}
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link href={`/ask?doc=${document.id}`} className={buttonClass("primary")}>
                      Ask a question
                    </Link>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setEditing(document.id);
                        setTitle(document.title);
                      }}
                    >
                      Rename
                    </Button>
                    <Button
                      variant="danger"
                      onClick={async () => {
                        if (!token || !window.confirm(`Delete ${document.title}?`)) return;
                        await client.remove(token, document.id);
                        setDocuments((current) => current.filter((item) => item.id !== document.id));
                        setSelected((current) => current.filter((item) => item !== document.id));
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function Status({ status }: { status: string }) {
  const ready = status === "ready";
  const failed = status === "error";
  const tone = ready ? "bg-emerald-50 text-emerald-800" : failed ? "bg-red-50 text-red-700" : "bg-blue-50 text-blue-800";
  const label = ready ? "Ready" : failed ? "Needs attention" : "Processing";
  return <span className={`rounded-full px-2 py-1 font-semibold ${tone}`}>{label}</span>;
}
