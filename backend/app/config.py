import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")

# Vercel functions can write only under /tmp. Local runs keep files in backend/data.
ON_VERCEL = os.getenv("VERCEL") == "1"
DATA_DIR = Path("/tmp/doculens") if ON_VERCEL else BACKEND_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "samples"
IDF_DIR = DATA_DIR / "idf"

for folder in (DATA_DIR, UPLOAD_DIR, SAMPLE_DIR, IDF_DIR):
    folder.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/doculens.db")
if DATABASE_URL.startswith("sqlite:///./"):
    DATABASE_URL = "sqlite:///" + str(DATA_DIR / DATABASE_URL.split("/")[-1])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PAGES = 200
MAX_DOCUMENTS = 5

DISCLAIMER = (
    "DocuLens provides information based on uploaded documents. It is not legal, "
    "financial, medical, employment, or professional advice. Verify important "
    "decisions with the official source or a qualified professional."
)

SYSTEM_INSTRUCTION = (
    "Answer only from the supplied document context. If the context does not contain "
    "the answer, say that the information was not found. Never invent dates, fees, "
    "requirements, policies, exceptions, or conclusions."
)

NOT_FOUND_MESSAGE = (
    "I could not find enough evidence in the uploaded documents to answer this confidently."
)

CATEGORIES = [
    "University document",
    "Research paper",
    "Rental agreement",
    "Policy or handbook",
    "Insurance document",
    "Technical manual",
    "Government form",
    "Business report",
    "Financial document",
    "Other",
]

CATEGORY_QUESTIONS = {
    "University document": [
        "What is the withdrawal deadline?",
        "What are the attendance requirements?",
        "What documents are required?",
        "What is the tuition refund schedule?",
        "What GPA places a student on academic probation?",
    ],
    "Research paper": [
        "What is the main research question?",
        "What methodology was used?",
        "What were the main findings?",
        "What are the limitations?",
    ],
    "Rental agreement": [
        "What is the monthly rent?",
        "When does the lease expire?",
        "What is the security deposit?",
        "What happens if the tenant ends the lease early?",
        "What are the pet rules?",
    ],
    "Policy or handbook": [
        "How much paid time off do employees accrue?",
        "What is the 401(k) match?",
        "How many days can employees work remotely?",
        "How much notice should a resigning employee give?",
    ],
    "Insurance document": [
        "What is the deductible?",
        "What does this policy cover?",
        "What exclusions apply?",
        "How do I file a claim?",
    ],
    "Technical manual": [
        "How do I install the product?",
        "What are the safety warnings?",
        "How do I troubleshoot this error?",
        "What is the warranty period?",
    ],
    "Government form": [
        "Who must sign this form?",
        "What is the submission deadline?",
        "What documents must be attached?",
        "Where is the completed form sent?",
    ],
    "Business report": [
        "What were the main results?",
        "What risks are identified?",
        "What actions are recommended?",
        "Which period does this report cover?",
    ],
    "Financial document": [
        "What is the total amount due?",
        "What period does this statement cover?",
        "What fees are listed?",
        "When is payment due?",
    ],
    "Other": [
        "What is this document about?",
        "What are the key dates?",
        "What actions are required?",
        "What information is missing?",
    ],
}

PROCESSING_STEPS = [
    ("uploading", "Uploading document"),
    ("extracting", "Extracting text"),
    ("classifying", "Detecting document type"),
    ("splitting", "Splitting content into sections"),
    ("embedding", "Creating embeddings"),
    ("indexing", "Indexing document"),
    ("ready", "Ready for questions"),
]
