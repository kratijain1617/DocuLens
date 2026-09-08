from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    category = Column(String, nullable=False, default="Other")
    category_source = Column(String, nullable=False, default="auto")
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    extracted_text = Column(Text, default="")
    processing_status = Column(String, default="uploading", index=True)
    error_message = Column(Text, nullable=True)
    storage_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    section = Column(String, default="")
    text = Column(Text, nullable=False)
    embedding = Column(Text, default="")
    start_position = Column(Integer, default=0)
    end_position = Column(Integer, default=0)

    document = relationship("Document", back_populates="chunks")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    documents = relationship("QuestionDocument", back_populates="question", cascade="all, delete-orphan")


class QuestionDocument(Base):
    __tablename__ = "question_documents"

    question_id = Column(String, ForeignKey("questions.id"), primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"), primary_key=True)

    question = relationship("Question", back_populates="documents")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, default="")
    confidence_score = Column(Float, default=0)
    answer_status = Column(String, nullable=False)
    payload = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)

    question = relationship("Question", back_populates="answers")
    citations = relationship("Citation", back_populates="answer", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String, primary_key=True)
    answer_id = Column(String, ForeignKey("answers.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    section = Column(String, default="")
    quoted_text = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0)

    answer = relationship("Answer", back_populates="citations")
    document = relationship("Document")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (UniqueConstraint("user_id", "id"),)

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    summary = Column(Text, default="")
    results = Column(Text, default="")
