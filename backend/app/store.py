import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import MAX_PAGES
from app.models import Document, DocumentChunk
from app.pipeline import (
    classify_text,
    cosine,
    embed_text,
    embed_texts,
    extract_pdf,
    fit_idf,
    load_idf,
    save_idf,
    split_sections,
    stems,
    tokenize,
)

STOPWORDS = {
    "what", "is", "the", "a", "an", "of", "to", "do", "i", "me", "my", "if", "does", "how",
    "are", "was", "were", "when", "where", "which", "who", "why", "in", "on", "for", "and",
    "or", "this", "that", "these", "those", "about", "please", "tell", "explain", "document",
    "documents", "agreement", "policy", "manual", "paper", "handbook", "something", "anything",
    "mentioned", "mention", "not", "happen", "happens", "did", "can", "could", "would",
    "should", "there", "their", "from", "with", "into", "than", "then", "them", "they", "you",
    "your", "our", "we", "be", "by", "at", "it", "its", "as", "before", "after", "during",
    "within", "each", "every", "per", "up", "out", "only", "also", "have", "has", "had",
    "will", "just", "more", "most", "other", "another", "such", "no", "nor", "but", "so",
    "very", "using", "used", "use", "based", "make", "made", "give", "given", "get", "across",
    "between", "both", "all", "any", "some", "am", "im", "please", "show", "find", "need",
}


def content_terms(question: str) -> list[str]:
    terms = []
    for token in tokenize(question):
        if token in STOPWORDS or len(token) < 3 and not any(ch.isdigit() for ch in token):
            continue
        rooted = stems(token)[0]
        if rooted not in STOPWORDS:
            terms.append(rooted)
    return terms


def term_recall(terms: list[str], text: str) -> float:
    if not terms:
        return 0.0
    present = set(stems(text))
    return sum(1 for term in terms if term in present) / len(terms)


def process_document(db: Session, document_id: str) -> None:
    document = db.get(Document, document_id)
    if document is None:
        return
    try:
        document.processing_status = "extracting"
        document.error_message = None
        db.commit()

        extracted = extract_pdf(Path(document.storage_path), document.title)
        if extracted["page_count"] > MAX_PAGES:
            raise ValueError(
                f"This PDF has {extracted['page_count']} pages. DocuLens can process up to {MAX_PAGES} pages."
            )
        document.page_count = extracted["page_count"]
        document.extracted_text = extracted["extracted_text"]
        document.processing_status = "classifying"
        db.commit()

        if document.category_source != "manual":
            category, source = classify_text(document.title, extracted["extracted_text"])
            document.category = category
            document.category_source = source

        document.processing_status = "splitting"
        db.commit()
        pieces = split_sections(extracted["pages"])
        if not pieces:
            raise ValueError("The PDF did not contain any text sections to index.")

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
        for piece in pieces:
            db.add(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    page_number=piece["page_number"],
                    section=piece["section"],
                    text=piece["text"],
                    embedding="",
                    start_position=piece["start_position"],
                    end_position=piece["end_position"],
                )
            )
        document.chunk_count = len(pieces)
        document.processing_status = "embedding"
        db.commit()

        document.processing_status = "indexing"
        db.commit()
        refit_user_embeddings(db, document.user_id)
        document = db.get(Document, document_id)
        document.processing_status = "ready"
        document.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document_id)
        if document:
            document.processing_status = "error"
            message = str(exc).strip() or "We could not read this PDF."
            document.error_message = message[:500]
            db.commit()


def refit_user_embeddings(db: Session, user_id: str) -> None:
    chunks = (
        db.query(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.user_id == user_id)
        .all()
    )
    if not chunks:
        save_idf(user_id, {})
        return
    corpus = [f"{chunk.section}\n{chunk.text}" for chunk in chunks]
    idf = fit_idf(corpus)
    vectors = embed_texts(corpus, idf)
    for chunk, vector in zip(chunks, vectors):
        chunk.embedding = json.dumps(vector)
    save_idf(user_id, idf)
    db.commit()


def chunk_views(db: Session, document_ids: list[str]) -> list[dict]:
    rows = (
        db.query(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(DocumentChunk.document_id.in_(document_ids))
        .all()
    )
    views = []
    for chunk, document in rows:
        try:
            vector = json.loads(chunk.embedding) if chunk.embedding else []
        except json.JSONDecodeError:
            vector = []
        views.append(
            {
                "id": chunk.id,
                "document_id": document.id,
                "document_name": document.file_name,
                "title": document.title,
                "category": document.category,
                "page_number": chunk.page_number,
                "section": chunk.section or "Document",
                "text": chunk.text,
                "embedding": vector,
                "start_position": chunk.start_position,
                "end_position": chunk.end_position,
            }
        )
    return views


def retrieve(question: str, chunks: list[dict], user_id: str, selected_page: int | None = None, limit: int = 6) -> list[dict]:
    if not chunks:
        return []
    idf = load_idf(user_id) or {}
    query_vector = embed_text(question, idf)
    terms = content_terms(question)
    scored = []
    for chunk in chunks:
        lexical = term_recall(terms, f"{chunk['section']} {chunk['text']}")
        phrase_bonus = 0.0
        lowered = f"{chunk['section']} {chunk['text']}".lower()
        raw_terms = [token for token in tokenize(question) if token not in STOPWORDS]
        for left, right in zip(raw_terms, raw_terms[1:]):
            if f"{left} {right}" in lowered:
                phrase_bonus += 0.12
        vector_score = cosine(query_vector, chunk["embedding"]) if chunk["embedding"] else 0.0
        if vector_score < 0:
            vector_score = 0.0
        section_bonus = 0.08 if term_recall(terms, chunk["section"]) >= 0.5 and terms else 0.0
        page_bonus = 0.04 if selected_page and chunk["page_number"] == selected_page else 0.0
        hybrid = min(1.0, 0.42 * min(vector_score, 1) + 0.46 * lexical + phrase_bonus + section_bonus + page_bonus)
        scored.append({**chunk, "score": round(hybrid, 4), "recall": lexical})
    scored.sort(key=lambda item: item["score"], reverse=True)
    qualified = [item for item in scored if item["score"] >= 0.18 or item["recall"] >= 0.5]
    return (qualified or scored)[:limit]
