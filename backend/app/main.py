import hashlib
import json
import re
import secrets
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import (
    CATEGORIES,
    CORS_ORIGINS,
    DATA_DIR,
    DISCLAIMER,
    MAX_DOCUMENTS,
    MAX_UPLOAD_BYTES,
    PROCESSING_STEPS,
    SAMPLE_DIR,
    UPLOAD_DIR,
)
from app.database import get_db, init_db
from app.evaluation import EVAL_ITEMS
from app.models import Answer, Citation, Document, EvaluationRun, Question, QuestionDocument, Session as AuthSession, User
from app.pipeline import compact, ensure_sample_pdfs, stems, suggested_questions
from app.qa import answer_with_optional_llm, compare_documents, expand_question, summarize_document
from app.sample_docs import SAMPLE_DOCUMENTS
from app.store import chunk_views, process_document, retrieve

app = FastAPI(title="DocuLens API", version="1.0.0")
_demo_lock = threading.Lock()

origins = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()] if CORS_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    ensure_sample_pdfs()


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RenameRequest(BaseModel):
    title: str


class AskRequest(BaseModel):
    document_ids: list[str] = Field(default_factory=list)
    user_question: str
    conversation_history: list[dict] = Field(default_factory=list)
    selected_page: int | None = None
    document_category: str | None = None


class CompareRequest(BaseModel):
    document_ids: list[str]
    user_question: str


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{digest.hex()}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, bytes.fromhex(salt_hex))
    return secrets.compare_digest(candidate, f"{salt_hex}:{digest_hex}")


def _password_error(password: str) -> str | None:
    if len(password) < 8:
        return "Use at least 8 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Include at least one letter and one number."
    return None


def _clean_email(email: str) -> str:
    return email.strip().lower()


def _email_error(email: str) -> str | None:
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return "Enter a valid email address."
    return None


def _issue_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        )
    )
    db.commit()
    return token


def require_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sign in, or start a demo session, to continue.")
    token = authorization.split(" ", 1)[1].strip()
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    session = db.query(AuthSession).filter(AuthSession.token_hash == token_hash).one_or_none()
    if session is None or session.user is None:
        raise HTTPException(status_code=401, detail="Your session expired. Sign in again.")
    return session.user


def _public_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
        "is_demo": user.password_hash is None,
    }


def _question_count(db: Session, document_id: str) -> int:
    return db.query(QuestionDocument).filter(QuestionDocument.document_id == document_id).count()


def _public_document(db: Session, document: Document) -> dict:
    return {
        "id": document.id,
        "title": document.title,
        "file_name": document.file_name,
        "category": document.category,
        "category_source": document.category_source,
        "page_count": document.page_count or 0,
        "chunk_count": document.chunk_count or 0,
        "processing_status": document.processing_status,
        "error_message": document.error_message,
        "created_at": document.created_at.isoformat(),
        "question_count": _question_count(db, document.id),
        "suggested_questions": suggested_questions(document.category),
        "steps": [{"id": step_id, "label": label} for step_id, label in PROCESSING_STEPS],
    }


def _owned_document(db: Session, user: User, document_id: str) -> Document:
    document = db.get(Document, document_id)
    if document is None or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="That document is not in your library.")
    return document


def _delete_document(db: Session, document: Document) -> None:
    db.query(Citation).filter(Citation.document_id == document.id).delete()
    db.query(QuestionDocument).filter(QuestionDocument.document_id == document.id).delete()
    path = Path(document.storage_path)
    db.delete(document)
    db.commit()
    if path.exists() and SAMPLE_DIR not in path.parents and path.parent != SAMPLE_DIR:
        path.unlink(missing_ok=True)


def _create_document_from_path(db: Session, user: User, source: Path, title: str, file_name: str, category: str | None) -> Document:
    if db.query(Document).filter(Document.user_id == user.id).count() >= MAX_DOCUMENTS:
        raise HTTPException(
            status_code=400,
            detail="You can keep up to 5 documents in a session. Delete one to upload another.",
        )
    document_id = str(uuid.uuid4())
    destination_dir = UPLOAD_DIR / user.id
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{document_id}.pdf"
    shutil.copy(source, destination)
    manual = category if category in CATEGORIES else None
    document = Document(
        id=document_id,
        user_id=user.id,
        title=title.strip() or Path(file_name).stem,
        file_name=file_name,
        category=manual or "Other",
        category_source="manual" if manual else "auto",
        processing_status="uploading",
        storage_path=str(destination),
        created_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()
    return document


def _demo_user(db: Session) -> User:
    email = "demo@doculens.app"
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        user = User(id=str(uuid.uuid4()), name="Demo Reader", email=email, password_hash=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _reset_demo_library(db: Session, user: User) -> None:
    for document in list(user.documents):
        _delete_document(db, document)
    ensure_sample_pdfs()
    for sample in SAMPLE_DOCUMENTS:
        document = _create_document_from_path(
            db,
            user,
            SAMPLE_DIR / sample["file_name"],
            sample["title"],
            sample["file_name"],
            sample["category"],
        )
        process_document(db, document.id)


@app.get("/api/health")
def health():
    return {"status": "ok", "name": "DocuLens", "disclaimer": DISCLAIMER}


@app.post("/api/auth/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    name = payload.name.strip()
    email = _clean_email(payload.email)
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Enter your name so the library knows who it belongs to.")
    if message := _email_error(email):
        raise HTTPException(status_code=400, detail=message)
    if payload.confirm_password is not None and payload.confirm_password != payload.password:
        raise HTTPException(status_code=400, detail="Those passwords do not match.")
    if message := _password_error(payload.password):
        raise HTTPException(status_code=400, detail=message)
    if db.query(User).filter(User.email == email).one_or_none():
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        password_hash=_hash_password(payload.password),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": _issue_session(db, user), "user": _public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = _clean_email(payload.email)
    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None or not user.password_hash or not _check_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="That email and password do not match.")
    return {"token": _issue_session(db, user), "user": _public_user(user)}


@app.post("/api/auth/demo")
def start_demo(db: Session = Depends(get_db)):
    with _demo_lock:
        user = _demo_user(db)
        _reset_demo_library(db, user)
        return {"token": _issue_session(db, user), "user": _public_user(user)}


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if authorization and authorization.lower().startswith("bearer "):
        token_hash = hashlib.sha256(authorization.split(" ", 1)[1].strip().encode("utf-8")).hexdigest()
        db.query(AuthSession).filter(AuthSession.token_hash == token_hash).delete()
        db.commit()
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: User = Depends(require_user)):
    return _public_user(user)


@app.get("/api/documents")
def list_documents(user: User = Depends(require_user), db: Session = Depends(get_db)):
    documents = (
        db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()
    )
    return {"documents": [_public_document(db, document) for document in documents], "categories": CATEGORIES}


@app.get("/api/documents/{document_id}")
def get_document(document_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return _public_document(db, _owned_document(db, user, document_id))


@app.get("/api/documents/{document_id}/file")
def download_document(document_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    document = _owned_document(db, user, document_id)
    path = Path(document.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="The original PDF is no longer available.")
    return FileResponse(path, media_type="application/pdf", filename=document.file_name)


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("Auto-detect"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if db.query(Document).filter(Document.user_id == user.id).count() >= MAX_DOCUMENTS:
        raise HTTPException(
            status_code=400,
            detail="You can keep up to 5 documents in a session. Delete one to upload another.",
        )
    filename = Path(file.filename or "document.pdf").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files can be uploaded.")
    payload = await file.read()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="This file is larger than 20 MB.")
    if not payload.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="That file does not look like a PDF. Choose a .pdf file.")
    document_id = str(uuid.uuid4())
    destination_dir = UPLOAD_DIR / user.id
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{document_id}.pdf"
    destination.write_bytes(payload)
    manual = category if category in CATEGORIES else None
    document = Document(
        id=document_id,
        user_id=user.id,
        title=(title or Path(filename).stem).strip()[:180],
        file_name=filename,
        category=manual or "Other",
        category_source="manual" if manual else "auto",
        processing_status="uploading",
        storage_path=str(destination),
        created_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()

    def _run():
        from app.database import SessionLocal

        session = SessionLocal()
        try:
            process_document(session, document_id)
        finally:
            session.close()

    threading.Thread(target=_run, daemon=True).start()
    db.refresh(document)
    return _public_document(db, document)


@app.patch("/api/documents/{document_id}")
def rename_document(document_id: str, payload: RenameRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    document = _owned_document(db, user, document_id)
    title = payload.title.strip()
    if len(title) < 2:
        raise HTTPException(status_code=400, detail="Give the document a title of at least 2 characters.")
    document.title = title[:180]
    db.commit()
    return _public_document(db, document)


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    document = _owned_document(db, user, document_id)
    _delete_document(db, document)
    from app.store import refit_user_embeddings

    refit_user_embeddings(db, user.id)
    return {"ok": True}


@app.get("/api/documents/{document_id}/history")
def document_history(document_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    document = _owned_document(db, user, document_id)
    links = db.query(QuestionDocument).filter(QuestionDocument.document_id == document.id).all()
    question_ids = [link.question_id for link in links]
    questions = (
        db.query(Question).filter(Question.id.in_(question_ids)).order_by(Question.created_at.asc()).all()
        if question_ids
        else []
    )
    history = []
    for question in questions:
        answer = question.answers[-1] if question.answers else None
        if answer is None:
            continue
        history.append(_public_answer(question, answer))
    return {"history": history}


@app.post("/api/documents/{document_id}/summarize")
def summarize(document_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)):
    document = _owned_document(db, user, document_id)
    if document.processing_status != "ready":
        raise HTTPException(status_code=400, detail=document.error_message or "This document is not ready for questions yet.")
    views = chunk_views(db, [document.id])
    summary = summarize_document(
        {"id": document.id, "file_name": document.file_name, "title": document.title, "category": document.category},
        views,
    )
    return summary


def _public_answer(question: Question, answer: Answer) -> dict:
    return {
        "id": answer.id,
        "question_id": question.id,
        "question": question.question,
        "answer": answer.answer,
        "explanation": answer.explanation or "",
        "confidence": answer.confidence_score,
        "answer_status": answer.answer_status,
        "citations": [
            {
                "document_id": citation.document_id,
                "document_name": citation.document.file_name if citation.document else "",
                "page_number": citation.page_number,
                "section": citation.section,
                "quoted_text": citation.quoted_text,
                "relevance_score": citation.relevance_score,
            }
            for citation in answer.citations
        ],
        "important_conditions": json.loads(answer.payload or "{}").get("important_conditions", []),
        "related_sections": json.loads(answer.payload or "{}").get("related_sections", []),
        "follow_up_questions": json.loads(answer.payload or "{}").get("follow_up_questions", []),
        "created_at": answer.created_at.isoformat(),
    }


def _save_answer(db: Session, user: User, question_text: str, document_ids: list[str], result: dict) -> dict:
    question = Question(
        id=str(uuid.uuid4()),
        user_id=user.id,
        question=question_text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(question)
    db.flush()
    for document_id in document_ids:
        db.add(QuestionDocument(question_id=question.id, document_id=document_id))
    answer = Answer(
        id=str(uuid.uuid4()),
        question_id=question.id,
        answer=result["answer"],
        explanation=result.get("explanation") or "",
        confidence_score=result["confidence"],
        answer_status=result["answer_status"],
        payload=json.dumps(
            {
                "important_conditions": result.get("important_conditions", []),
                "related_sections": result.get("related_sections", []),
                "follow_up_questions": result.get("follow_up_questions", []),
            }
        ),
        created_at=datetime.now(timezone.utc),
    )
    db.add(answer)
    db.flush()
    for citation in result.get("citations", []):
        db.add(
            Citation(
                id=str(uuid.uuid4()),
                answer_id=answer.id,
                document_id=citation["document_id"],
                page_number=citation["page_number"],
                section=citation.get("section") or "",
                quoted_text=citation["quoted_text"],
                relevance_score=citation.get("relevance_score") or 0,
            )
        )
    db.commit()
    db.refresh(answer)
    return _public_answer(question, answer)


@app.post("/api/ask")
def ask(payload: AskRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    question = payload.user_question.strip()
    if len(question) < 3:
        raise HTTPException(status_code=400, detail="Enter a question to search the document.")
    if not payload.document_ids:
        raise HTTPException(status_code=400, detail="Select a document before asking.")
    documents = [_owned_document(db, user, document_id) for document_id in payload.document_ids]
    not_ready = [document.title for document in documents if document.processing_status != "ready"]
    if not_ready:
        raise HTTPException(status_code=400, detail=f"{not_ready[0]} is not ready for questions yet.")
    category = payload.document_category or documents[0].category
    expanded = expand_question(question, payload.conversation_history)
    views = chunk_views(db, [document.id for document in documents])
    retrieved = retrieve(expanded, views, user.id, payload.selected_page)
    result = answer_with_optional_llm(question, retrieved, category, payload.conversation_history, payload.selected_page)
    saved = _save_answer(db, user, question, [document.id for document in documents], result)
    return saved


@app.post("/api/compare")
def compare(payload: CompareRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    question = payload.user_question.strip()
    if len(payload.document_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least two documents to compare.")
    if len(question) < 3:
        raise HTTPException(status_code=400, detail="Enter a comparison question.")
    documents = [_owned_document(db, user, document_id) for document_id in payload.document_ids]
    groups = []
    for document in documents:
        if document.processing_status != "ready":
            raise HTTPException(status_code=400, detail=f"{document.title} is not ready for questions yet.")
        views = chunk_views(db, [document.id])
        retrieved = retrieve(question, views, user.id)
        groups.append(
            (
                {
                    "id": document.id,
                    "file_name": document.file_name,
                    "title": document.title,
                    "category": document.category,
                },
                retrieved,
            )
        )
    result = compare_documents(question, groups)
    flat_citations = [citation for column in result["documents"] for citation in column["citations"]]
    _save_answer(
        db,
        user,
        question,
        [document.id for document in documents],
        {
            "answer": result["summary"],
            "explanation": "Comparison across selected documents.",
            "confidence": result["confidence"],
            "answer_status": result["answer_status"],
            "citations": flat_citations,
            "important_conditions": [],
            "related_sections": [],
            "follow_up_questions": result["follow_up_questions"],
        },
    )
    return result


def _fact_recall(expected: str, actual: str) -> float:
    from app.store import STOPWORDS

    expected_terms = [term for term in stems(expected) if term not in STOPWORDS and len(term) > 2]
    if not expected_terms:
        return 0.0
    actual_terms = set(stems(actual))
    return sum(1 for term in expected_terms if term in actual_terms) / len(expected_terms)


@app.get("/api/evaluation/dataset")
def evaluation_dataset(user: User = Depends(require_user)):
    return {"items": EVAL_ITEMS, "count": len(EVAL_ITEMS)}


@app.post("/api/evaluation/run")
def run_evaluation(user: User = Depends(require_user), db: Session = Depends(get_db)):
    import time

    documents = {
        document.file_name: document
        for document in db.query(Document).filter(Document.user_id == user.id, Document.processing_status == "ready")
    }
    results = []
    for item in EVAL_ITEMS:
        started = time.perf_counter()
        document = documents.get(item["expected_document"])
        if document is None:
            results.append({**item, "ok": False, "error": "The expected demo document is not in this library.", "response_time_ms": 0})
            continue
        views = chunk_views(db, [document.id])
        retrieved = retrieve(item["question"], views, user.id)
        answer = answer_with_optional_llm(item["question"], retrieved, document.category)
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        blob = answer["answer"] + " " + " ".join(citation["quoted_text"] for citation in answer["citations"])
        if item["expected_status"] == "not_found":
            answer_correct = answer["answer_status"] == "not_found"
        elif item["expected_status"] == "conflicting_information":
            answer_correct = answer["answer_status"] == "conflicting_information" and all(fact in blob for fact in item["required_facts"])
        else:
            answer_correct = _fact_recall(item["expected_answer"], answer["answer"]) >= 0.55
        cited_pages = {
            citation["page_number"]
            for citation in answer["citations"]
            if citation["document_name"] == item["expected_document"]
        }
        expected_pages = item["expected_pages"]
        if item["expected_status"] == "not_found":
            page_correct = answer["answer_status"] == "not_found"
            citation_correct = answer["answer_status"] == "not_found" and not answer["citations"]
        else:
            page_correct = all(page in cited_pages for page in expected_pages)
            evidence = compact(item["expected_evidence"])
            evidence_ok = any(
                evidence and (evidence in compact(citation["quoted_text"]) or compact(citation["quoted_text"]) in evidence)
                for citation in answer["citations"]
            )
            citation_correct = page_correct and evidence_ok and any(
                citation["document_name"] == item["expected_document"] for citation in answer["citations"]
            )
        source = compact(document.extracted_text or "")
        if answer["citations"]:
            grounding = all(compact(citation["quoted_text"]) in source for citation in answer["citations"])
        else:
            grounding = answer["answer_status"] == "not_found"
        retrieved_pages = [chunk["page_number"] for chunk in retrieved]
        if item["expected_status"] == "not_found":
            retrieval_hit = answer["answer_status"] == "not_found"
        else:
            retrieval_hit = all(page in retrieved_pages for page in expected_pages)
        unsupported = answer["answer_status"] in {"supported", "partially_supported"} and (
            not grounding or item["expected_status"] == "not_found"
        )
        results.append(
            {
                "question": item["question"],
                "expected_answer": item["expected_answer"],
                "expected_document": item["expected_document"],
                "expected_page": item["expected_page"],
                "expected_evidence": item["expected_evidence"],
                "expected_status": item["expected_status"],
                "answer": answer["answer"],
                "answer_status": answer["answer_status"],
                "confidence": answer["confidence"],
                "citations": answer["citations"],
                "answer_correct": answer_correct,
                "citation_correct": citation_correct,
                "page_correct": page_correct,
                "grounded": grounding,
                "retrieval_hit": retrieval_hit,
                "unsupported": unsupported,
                "response_time_ms": elapsed,
            }
        )
    total = len(results) or 1

    def rate(key: str) -> float:
        return round(sum(1 for item in results if item.get(key)) / total, 4)

    summary = {
        "answer_correctness": rate("answer_correct"),
        "citation_correctness": rate("citation_correct"),
        "correct_page_rate": rate("page_correct"),
        "citation_grounding_rate": rate("grounded"),
        "retrieval_hit_rate": rate("retrieval_hit"),
        "unsupported_answer_rate": rate("unsupported"),
        "average_response_time_ms": round(sum(item.get("response_time_ms", 0) for item in results) / total, 1),
        "total": len(results),
    }
    run = EvaluationRun(
        id=str(uuid.uuid4()),
        user_id=user.id,
        summary=json.dumps(summary),
        results=json.dumps(results),
        created_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    return {"summary": summary, "results": results}

