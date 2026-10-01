"use client";

import { Button } from "@/components/ui";
import { Download, Maximize2, Minus, Plus } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = `${typeof window === "undefined" ? "" : window.location.origin}/pdf.worker.min.mjs`;

function compact(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

export function PdfViewer({
  file,
  page,
  pageCount,
  highlight,
  onPageChange,
  onDownload,
  fileName,
}: {
  file: Blob | null;
  page: number;
  pageCount?: number;
  highlight: string;
  onPageChange: (page: number) => void;
  onDownload?: () => void;
  fileName?: string;
}) {
  const [pages, setPages] = useState(pageCount || 0);
  const [scale, setScale] = useState(1.05);
  const [query, setQuery] = useState("");
  const [searchHit, setSearchHit] = useState("");
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [documentFile, setDocumentFile] = useState<{ data: Uint8Array } | null>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef<HTMLDivElement>(null);
  const bytesRef = useRef<Uint8Array | null>(null);

  const paint = useCallback(() => {
    const root = stageRef.current;
    if (!root) return;
    const spans = Array.from(root.querySelectorAll<HTMLSpanElement>(".react-pdf__Page__textContent span"));
    spans.forEach((span) => span.classList.remove("cite-hit"));
    const needle = compact(searchHit || highlight);
    if (!needle) return;
    let compactText = "";
    const map: number[] = [];
    spans.forEach((span, index) => {
      for (const char of (span.textContent || "").toLowerCase()) {
        if (/[a-z0-9]/.test(char)) {
          compactText += char;
          map.push(index);
        }
      }
    });
    const at = compactText.indexOf(needle);
    if (at < 0) return;
    const hits = new Set<number>();
    for (let index = at; index < at + needle.length && index < map.length; index += 1) hits.add(map[index]);
    const matched: HTMLSpanElement[] = [];
    spans.forEach((span, index) => {
      if (!hits.has(index)) return;
      span.classList.add("cite-hit");
      matched.push(span);
    });
    matched[0]?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [highlight, searchHit]);

  useEffect(() => {
    setSearchHit("");
  }, [highlight]);

  useEffect(() => {
    const timer = window.setTimeout(paint, 80);
    return () => window.clearTimeout(timer);
  }, [paint, ready]);

  useEffect(() => {
    let cancelled = false;
    setReady(false);
    setSearchHit("");
    if (!file) {
      bytesRef.current = null;
      setDocumentFile(null);
      return;
    }
    file.arrayBuffer().then((buffer) => {
      if (cancelled) return;
      const bytes = new Uint8Array(buffer);
      bytesRef.current = bytes;
      setDocumentFile({ data: bytes.slice() });
    });
    return () => {
      cancelled = true;
    };
  }, [file]);

  const safePage = Math.min(Math.max(page || 1, 1), pages || 1);

  async function search(event: React.FormEvent) {
    event.preventDefault();
    const needle = query.trim().toLowerCase();
    const bytes = bytesRef.current;
    if (!needle || !bytes) return;
    setError("");
    try {
      const task = pdfjs.getDocument({ data: bytes.slice() });
      const pdf = await task.promise;
      let found = 0;
      for (let index = 1; index <= pdf.numPages; index += 1) {
        const pdfPage = await pdf.getPage(index);
        const content = await pdfPage.getTextContent();
        const text = content.items.map((item) => ("str" in item ? item.str : "")).join(" ");
        if (text.toLowerCase().includes(needle)) {
          found = index;
          break;
        }
      }
      await pdf.destroy();
      if (found) {
        setSearchHit(query.trim());
        onPageChange(found);
      } else setError("That phrase was not found in this PDF.");
    } catch {
      setError("Search could not read this PDF.");
    }
  }

  return (
    <section ref={frameRef} className="flex h-full min-h-[520px] flex-col rounded-3xl border border-line bg-white shadow-card">
      <div className="flex flex-wrap items-center gap-2 border-b border-line px-3 py-3">
        <p className="mr-auto truncate text-sm font-semibold text-navy">{fileName || "Source PDF"}</p>
        <Button variant="secondary" className="h-9 w-9 px-0" onClick={() => onPageChange(Math.max(1, page - 1))} aria-label="Previous page">
          ‹
        </Button>
        <span className="text-xs font-medium text-slate-600">
          {page} / {pages || "–"}
        </span>
        <Button variant="secondary" className="h-9 w-9 px-0" onClick={() => onPageChange(pages ? Math.min(pages, page + 1) : page + 1)} aria-label="Next page">
          ›
        </Button>
        <Button variant="secondary" className="h-9 w-9 px-0" onClick={() => setScale((value) => Math.max(0.7, value - 0.15))} aria-label="Zoom out">
          <Minus size={14} />
        </Button>
        <Button variant="secondary" className="h-9 w-9 px-0" onClick={() => setScale((value) => Math.min(2.2, value + 0.15))} aria-label="Zoom in">
          <Plus size={14} />
        </Button>
        <Button
          variant="secondary"
          className="h-9 w-9 px-0"
          aria-label="Full screen"
          onClick={() => {
            if (!document.fullscreenElement) frameRef.current?.requestFullscreen();
            else document.exitFullscreen();
          }}
        >
          <Maximize2 size={14} />
        </Button>
        <Button variant="secondary" className="h-9 px-3" onClick={onDownload} disabled={!file}>
          <Download size={14} /> PDF
        </Button>
      </div>
      <form onSubmit={search} className="flex gap-2 border-b border-line px-3 py-2">
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setError("");
          }}
          placeholder="Search this document"
          className="w-full rounded-full border border-line px-3 py-1.5 text-sm outline-none"
          aria-label="Search within document"
        />
        <Button variant="secondary" type="submit">
          Find
        </Button>
      </form>
      {error ? <p className="px-3 pt-2 text-xs text-red-700">{error}</p> : null}
      <div ref={stageRef} className="min-h-0 flex-1 overflow-auto bg-slate-100 p-4">
        {documentFile ? (
          <Document
            file={documentFile}
            onLoadSuccess={(pdf) => {
              setPages(pdf.numPages);
              setReady(true);
              setError("");
            }}
            onLoadError={() => setError("The PDF could not be displayed.")}
            loading={<p className="text-sm text-slate-500">Opening the PDF…</p>}
          >
            {ready ? (
              <Page
                pageNumber={safePage}
                scale={scale}
                onRenderTextLayerSuccess={paint}
                renderAnnotationLayer={false}
                className="mx-auto shadow-card"
              />
            ) : null}
          </Document>
        ) : (
          <div className="grid h-full place-items-center text-sm text-slate-500">Select a document to open the source.</div>
        )}
      </div>
    </section>
  );
}
