from app.sample_docs import SAMPLE_DOCUMENTS


def _paragraph(file_name: str, page: int, section: str, index: int = 0) -> str:
    document = next(item for item in SAMPLE_DOCUMENTS if item["file_name"] == file_name)
    block = next(item for item in document["pages"][page - 1]["blocks"] if item["section"] == section)
    return block["paragraphs"][index]


def _join(file_name: str, page: int, section: str) -> str:
    document = next(item for item in SAMPLE_DOCUMENTS if item["file_name"] == file_name)
    block = next(item for item in document["pages"][page - 1]["blocks"] if item["section"] == section)
    return " ".join(block["paragraphs"])


RENTAL = "Apartment Rental Agreement.pdf"
UNIVERSITY = "University Student Policy Manual.pdf"
MANUAL = "Technical Product Manual.pdf"
PAPER = "Research Paper.pdf"
HANDBOOK = "Employee Handbook.pdf"


def _item(question, file_name, page, section, index=0, status="supported", pages=None, facts=None, answer=None):
    evidence = _paragraph(file_name, page, section, index) if answer is None else answer
    return {
        "question": question,
        "expected_answer": evidence if answer is None else answer,
        "expected_document": file_name,
        "expected_page": page,
        "expected_pages": pages or [page],
        "expected_evidence": evidence if answer is None else _paragraph(file_name, page, section, index),
        "expected_status": status,
        "required_facts": facts or [],
    }


EVAL_ITEMS = [
    _item("What is the security deposit?", RENTAL, 3, "Security Deposit", 0),
    _item("What is the monthly rent?", RENTAL, 3, "Monthly Rent", 0),
    _item("When does the lease expire?", RENTAL, 2, "Lease Term", 0),
    _item("What happens if the tenant ends the lease early?", RENTAL, 4, "Early Termination", 0),
    _item("What is the late fee?", RENTAL, 3, "Monthly Rent", 2),
    _item("What is the pet deposit?", RENTAL, 6, "Pets", 0),
    _item("What are the quiet hours?", RENTAL, 7, "House Rules", 0),
    {
        "question": "What is the course withdrawal deadline?",
        "expected_answer": "October 24, 2026 and October 17, 2026",
        "expected_document": UNIVERSITY,
        "expected_page": 2,
        "expected_pages": [2, 3],
        "expected_evidence": _paragraph(UNIVERSITY, 2, "Course Withdrawal", 0),
        "expected_status": "conflicting_information",
        "required_facts": ["October 24, 2026", "October 17, 2026"],
    },
    _item("What are the attendance requirements?", UNIVERSITY, 4, "Attendance Requirements", 0),
    _item("What documents are required?", UNIVERSITY, 5, "Required Documents", 0),
    _item("What is the tuition refund for the first week?", UNIVERSITY, 6, "Tuition Refunds", 0),
    _item("What GPA places a student on academic probation?", UNIVERSITY, 7, "Academic Standing", 0),
    _item("How do I install the product?", MANUAL, 3, "Installation", 0),
    _item("What are the safety warnings?", MANUAL, 2, "Safety Warnings", 0, answer=_join(MANUAL, 2, "Safety Warnings")),
    _item("How do I troubleshoot this error?", MANUAL, 5, "Troubleshooting", 1),
    _item("What is the warranty period?", MANUAL, 8, "Warranty", 0),
    _item("What is the main research question?", PAPER, 2, "Research Question", 0),
    _item("What methodology was used?", PAPER, 3, "Methodology", 0),
    _item("What were the main findings?", PAPER, 4, "Main Findings", 0),
    _item("What are the limitations?", PAPER, 6, "Limitations", 0),
    _item("How much paid time off do employees accrue?", HANDBOOK, 3, "Paid Time Off", 0),
    _item("What is the 401(k) match?", HANDBOOK, 4, "Benefits", 0),
    _item("How many days can employees work remotely?", HANDBOOK, 5, "Remote Work", 0),
    _item("How much notice should a resigning employee give?", HANDBOOK, 7, "Separation", 0),
    {
        "question": "What happens if I do something that is not mentioned in the agreement?",
        "expected_answer": "I could not find enough evidence in the uploaded documents to answer this confidently.",
        "expected_document": RENTAL,
        "expected_page": None,
        "expected_pages": [],
        "expected_evidence": "",
        "expected_status": "not_found",
        "required_facts": [],
    },
    {
        "question": "What color is the analyzer carrying case?",
        "expected_answer": "I could not find enough evidence in the uploaded documents to answer this confidently.",
        "expected_document": MANUAL,
        "expected_page": None,
        "expected_pages": [],
        "expected_evidence": "",
        "expected_status": "not_found",
        "required_facts": [],
    },
]
