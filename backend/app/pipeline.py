import json
import math
import re
import zlib
from collections import Counter
from pathlib import Path

import pymupdf
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from reportlab.lib.colors import Color, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.config import (
    CATEGORIES,
    CATEGORY_QUESTIONS,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    IDF_DIR,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    SAMPLE_DIR,
)
from app.sample_docs import SAMPLE_DOCUMENTS

NAVY = Color(14 / 255, 28 / 255, 54 / 255)
INK = Color(18 / 255, 32 / 255, 51 / 255)
MUTED = Color(100 / 255, 116 / 255, 139 / 255)
IRIS = Color(91 / 255, 75 / 255, 214 / 255)

DIM = 384
TOKEN_RE = re.compile(r"[a-z0-9]+")
DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE,
)

CLASSIFIER_KEYWORDS = {
    "University document": ["student", "withdrawal", "transcript", "gpa", "enrollment", "academic", "tuition", "semester", "registrar"],
    "Research paper": ["abstract", "methodology", "findings", "limitations", "research question", "annotators", "hypothesis"],
    "Rental agreement": ["lease", "tenant", "landlord", "security deposit", "monthly rent", "premises", "early termination"],
    "Policy or handbook": ["employee", "handbook", "paid time off", "401", "workplace", "human resources", "remote work"],
    "Insurance document": ["deductible", "policyholder", "premium", "coverage", "exclusion", "claimant"],
    "Technical manual": ["installation", "troubleshooting", "warranty", "specifications", "safety warnings", "calibration", "firmware"],
    "Government form": ["applicant", "department", "statute", "agency", "submission", "form number"],
    "Business report": ["revenue", "quarter", "board", "strategy", "market share", "stakeholders"],
    "Financial document": ["balance sheet", "fiscal", "assets", "liabilities", "invoice", "amount due"],
}

MISSING_TOPICS = {
    "University document": ["withdrawal", "attendance", "tuition", "probation", "appeal"],
    "Research paper": ["research question", "methodology", "findings", "limitations"],
    "Rental agreement": ["rent", "security deposit", "lease", "early termination", "pet"],
    "Policy or handbook": ["paid time off", "benefits", "remote", "conduct", "notice"],
    "Insurance document": ["deductible", "coverage", "exclusion", "claim"],
    "Technical manual": ["installation", "safety", "troubleshooting", "warranty"],
    "Government form": ["deadline", "signature", "attachment"],
    "Business report": ["results", "risks", "recommendation"],
    "Financial document": ["amount", "period", "fee", "payment"],
    "Other": ["date", "requirement", "contact"],
}


def sanitize_text(value: str) -> str:
    cleaned = value.replace("\x00", "")
    return "".join(ch for ch in cleaned if ch in "\n\t" or ord(ch) >= 32)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def tokenize(value: str) -> list[str]:
    return TOKEN_RE.findall(value.lower())


def stem(word: str) -> str:
    if len(word) <= 3:
        return word
    original = word
    if word.endswith("ies") and len(word) > 5:
        word = word[:-3] + "y"
    else:
        for suffix in ("ing", "ers", "er", "es", "ed", "s"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                if suffix == "s" and original.endswith(("ss", "us", "is", "ous")):
                    break
                word = word[: -len(suffix)]
                break
    if len(word) > 4 and word.endswith("e"):
        word = word[:-1]
    return word


def stems(value: str) -> list[str]:
    return [stem(token) for token in tokenize(value)]


def ensure_sample_pdfs() -> list[Path]:
    paths = []
    for document in SAMPLE_DOCUMENTS:
        path = SAMPLE_DIR / document["file_name"]
        if not path.exists():
            write_sample_pdf(document, path)
        paths.append(path)
    return paths


def write_sample_pdf(document: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.setTitle(document["title"])
    pdf.setAuthor("DocuLens Samples")
    width, height = letter
    for index, page in enumerate(document["pages"], start=1):
        pdf.setFillColor(NAVY)
        pdf.rect(0, height - 58, width, 58, fill=1, stroke=0)
        pdf.setFillColor(white)
        pdf.setFont("Times-Bold", 11)
        pdf.drawString(48, height - 34, document["title"])
        pdf.setFont("Times-Roman", 10)
        pdf.drawRightString(width - 48, height - 34, f"Page {index}")
        y = height - 92
        for block in page["blocks"]:
            pdf.setFillColor(NAVY)
            pdf.setFont("Times-Bold", 16)
            pdf.drawString(48, y, block["section"])
            y -= 8
            pdf.setStrokeColor(IRIS)
            pdf.setLineWidth(2)
            pdf.line(48, y, 168, y)
            y -= 22
            pdf.setFillColor(INK)
            pdf.setFont("Times-Roman", 12)
            for paragraph in block["paragraphs"]:
                for line in wrap_text(pdf, paragraph, "Times-Roman", 12, width - 96):
                    pdf.drawString(48, y, line)
                    y -= 17
                y -= 8
            y -= 8
        pdf.setFillColor(MUTED)
        pdf.setFont("Times-Italic", 9)
        pdf.drawString(48, 36, "Demonstration sample for DocuLens. Not an official policy, contract, or manual.")
        pdf.showPage()
    pdf.save()


def wrap_text(pdf: canvas.Canvas, text: str, font: str, size: int, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if pdf.stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def extract_pdf(path: Path, title: str = "") -> dict:
    document = pymupdf.open(path)
    try:
        if document.is_encrypted and document.needs_pass:
            raise ValueError("This PDF is password protected. Remove the password and upload it again.")
        page_count = document.page_count
        pages = []
        texts = []
        for number, page in enumerate(document, start=1):
            lines = _page_lines(page, title)
            sections = _group_sections(lines)
            page_text_parts = []
            blocks = []
            cursor = 0
            for section in sections:
                body = normalize_space(sanitize_text(" ".join(section["lines"])))
                if not body and section["section"] == "Document":
                    continue
                heading = section["section"]
                start = cursor
                piece = f"{heading}\n{body}".strip()
                cursor += len(piece) + 2
                blocks.append(
                    {
                        "section": heading,
                        "text": body,
                        "start_position": start,
                        "end_position": start + len(body),
                    }
                )
                page_text_parts.append(piece)
            full_text = "\n\n".join(page_text_parts).strip()
            texts.append(full_text)
            pages.append({"page_number": number, "blocks": blocks, "text": full_text})
        extracted = "\f".join(texts)
        if compact(extracted) == "":
            raise ValueError(
                "No selectable text was found. Scanned image PDFs need a text layer, and DocuLens does not OCR documents yet."
            )
        return {"page_count": page_count, "pages": pages, "extracted_text": sanitize_text(extracted)}
    finally:
        document.close()


def _page_lines(page, title: str) -> list[dict]:
    payload = page.get_text("dict")
    lines = []
    for block in payload.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = sanitize_text("".join(span.get("text", "") for span in spans)).strip()
            if not text:
                continue
            if text == title or re.fullmatch(r"Page \d+", text):
                continue
            if text.startswith("Demonstration sample for DocuLens"):
                continue
            size = max((span.get("size", 12) for span in spans), default=12)
            lines.append({"text": text, "size": size})
    return lines


def _group_sections(lines: list[dict]) -> list[dict]:
    sections = []
    current = {"section": "Document", "lines": []}
    for line in lines:
        is_heading = line["size"] >= 15 and len(line["text"]) <= 80 and not line["text"].endswith(".")
        if is_heading:
            if current["lines"] or current["section"] != "Document":
                sections.append(current)
            current = {"section": line["text"], "lines": []}
        else:
            current["lines"].append(line["text"])
    if current["lines"] or current["section"] != "Document":
        sections.append(current)
    return sections or [{"section": "Document", "lines": []}]


def classify_text(title: str, text: str, manual_category: str | None = None) -> tuple[str, str]:
    if manual_category in CATEGORIES and manual_category != "Auto-detect":
        return manual_category, "manual"
    haystack = f"{title}\n{text[:6000]}".lower()
    scores = {}
    for category, keywords in CLASSIFIER_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in haystack:
                score += 2 if " " in keyword else 1
        scores[category] = score
    best = max(scores, key=scores.get)
    if scores[best] < 2:
        return "Other", "auto"
    return best, "auto"


def split_sections(pages: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120, separators=["\n\n", "\n", ". ", " "])
    chunks = []
    for page in pages:
        for block in page["blocks"]:
            body = block["text"].strip()
            if not body:
                continue
            pieces = splitter.split_text(body) or [body]
            search_from = 0
            for piece in pieces:
                start = body.find(piece[:80], search_from)
                if start < 0:
                    start = block["start_position"]
                else:
                    start = block["start_position"] + start
                search_from = max(search_from, start + 1)
                chunks.append(
                    {
                        "page_number": page["page_number"],
                        "section": block["section"] or "Document",
                        "text": piece.strip(),
                        "start_position": start,
                        "end_position": start + len(piece),
                    }
                )
    return chunks


def suggested_questions(category: str) -> list[str]:
    return CATEGORY_QUESTIONS.get(category, CATEGORY_QUESTIONS["Other"])


def _hash_index(token: str) -> tuple[int, int]:
    digest = zlib.crc32(token.encode("utf-8")) & 0xFFFFFFFF
    return digest % DIM, 1 if (digest >> 8) & 1 else -1


def fit_idf(texts: list[str]) -> dict[str, float]:
    document_count = max(1, len(texts))
    df = Counter()
    for text in texts:
        df.update(set(tokenize(text)))
    return {term: math.log((1 + document_count) / (1 + freq)) + 1.0 for term, freq in df.items()}


def embed_text(text: str, idf: dict[str, float]) -> list[float]:
    if EMBEDDING_PROVIDER == "openai" and OPENAI_API_KEY:
        vector = _openai_embed(text)
        if vector:
            return vector
    if EMBEDDING_PROVIDER == "sentence-transformers":
        vector = _sentence_embed(text)
        if vector:
            return vector
    return _local_embed(text, idf)


def embed_texts(texts: list[str], idf: dict[str, float]) -> list[list[float]]:
    if EMBEDDING_PROVIDER == "openai" and OPENAI_API_KEY:
        vectors = _openai_embed_many(texts)
        if vectors:
            return vectors
    if EMBEDDING_PROVIDER == "sentence-transformers":
        vectors = _sentence_embed_many(texts)
        if vectors:
            return vectors
    return [_local_embed(text, idf) for text in texts]


def _local_embed(text: str, idf: dict[str, float]) -> list[float]:
    vector = np.zeros(DIM, dtype=np.float32)
    tokens = tokenize(text)
    if not tokens:
        return vector.tolist()
    counts = Counter(tokens)
    for token, count in counts.items():
        weight = (1.0 + math.log(count)) * idf.get(token, 1.0)
        index, sign = _hash_index(token)
        vector[index] += sign * weight
    for left, right in zip(tokens, tokens[1:]):
        phrase = f"{left}_{right}"
        weight = 1.4 * idf.get(left, 1.0)
        index, sign = _hash_index(phrase)
        vector[index] += sign * weight
    norm = float(np.linalg.norm(vector))
    if norm > 0:
        vector /= norm
    return vector.tolist()


def _openai_embed(text: str) -> list[float] | None:
    vectors = _openai_embed_many([text])
    return vectors[0] if vectors else None


def _openai_embed_many(texts: list[str]) -> list[list[float]] | None:
    import httpx

    try:
        response = httpx.post(
            f"{OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": EMBEDDING_MODEL, "input": texts},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()["data"]
        data.sort(key=lambda item: item["index"])
        return [item["embedding"] for item in data]
    except Exception:
        return None


_st_model = None


def _sentence_embed(text: str) -> list[float] | None:
    vectors = _sentence_embed_many([text])
    return vectors[0] if vectors else None


def _sentence_embed_many(texts: list[str]) -> list[list[float]] | None:
    global _st_model
    try:
        from sentence_transformers import SentenceTransformer

        if _st_model is None:
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        vectors = _st_model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]
    except Exception:
        return None


def save_idf(user_id: str, idf: dict[str, float]) -> None:
    path = IDF_DIR / f"{user_id}.json"
    path.write_text(json.dumps(idf), encoding="utf-8")


def load_idf(user_id: str) -> dict[str, float] | None:
    path = IDF_DIR / f"{user_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def cosine(left: list[float], right: list[float]) -> float:
    a = np.asarray(left, dtype=np.float32)
    b = np.asarray(right, dtype=np.float32)
    if a.shape != b.shape or a.size == 0:
        return 0.0
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
