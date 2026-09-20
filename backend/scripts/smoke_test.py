"""Run the demo library through extraction, classification, answering, and evaluation."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import classify_text, extract_pdf
from app.sample_docs import SAMPLE_DOCUMENTS


def main():
    failures = []
    with TestClient(app) as client:
        for sample in SAMPLE_DOCUMENTS:
            extracted = extract_pdf(ROOT / "data" / "samples" / sample["file_name"], sample["title"])
            joined = extracted["extracted_text"]
            for page in sample["pages"]:
                for block in page["blocks"]:
                    for paragraph in block["paragraphs"]:
                        compact_paragraph = "".join(ch for ch in paragraph.lower() if ch.isalnum())
                        compact_doc = "".join(ch for ch in joined.lower() if ch.isalnum())
                        if compact_paragraph not in compact_doc:
                            failures.append(f"Missing paragraph in {sample['file_name']}: {paragraph[:80]}")
                    if block["section"] not in joined:
                        failures.append(f"Missing section {block['section']} in {sample['file_name']}")
            category, _source = classify_text(sample["title"], joined)
            if category != sample["category"]:
                failures.append(f"Classified {sample['file_name']} as {category}, expected {sample['category']}")

        demo = client.post("/api/auth/demo")
        if demo.status_code != 200:
            print(demo.text)
            raise SystemExit(1)
        headers = {"Authorization": f"Bearer {demo.json()['token']}"}
        library = client.get("/api/documents", headers=headers)
        documents = library.json()["documents"]
        print(f"Demo documents: {len(documents)}")
        for document in documents:
            print(f"  {document['title']} | {document['category']} | {document['page_count']} pages | {document['chunk_count']} chunks | {document['processing_status']}")
            if document["processing_status"] != "ready":
                failures.append(f"{document['title']} not ready: {document['error_message']}")

        evaluation = client.post("/api/evaluation/run", headers=headers)
        body = evaluation.json()
        summary = body["summary"]
        print("\nEvaluation")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        for item in body["results"]:
            if not (item["answer_correct"] and item["citation_correct"] and item["retrieval_hit"] and item["grounded"]):
                print("\nMISS:", item["question"])
                print("  status:", item["answer_status"], "expected:", item["expected_status"])
                print("  answer:", item["answer"][:240])
                print("  pages:", [citation["page_number"] for citation in item["citations"]], "expected", item.get("expected_page"))
                print("  flags:", {key: item[key] for key in ("answer_correct", "citation_correct", "page_correct", "retrieval_hit", "grounded")})
                failures.append(item["question"])

        rental = next(document for document in documents if "Rental" in document["title"])
        missing = client.post(
            "/api/ask",
            headers=headers,
            json={"document_ids": [rental["id"]], "user_question": "What happens if I do something that is not mentioned in the agreement?"},
        )
        if missing.json()["answer_status"] != "not_found":
            failures.append("Demo not-found question did not return not_found")
        deposit = client.post(
            "/api/ask",
            headers=headers,
            json={"document_ids": [rental["id"]], "user_question": "What is the security deposit?"},
        )
        deposit_body = deposit.json()
        print("\nSecurity deposit:", deposit_body["answer"])
        if deposit_body["citations"]:
            print("  citation page", deposit_body["citations"][0]["page_number"], deposit_body["citations"][0]["section"])

        paper = next(document for document in documents if document["title"] == "Research Paper")
        summary = client.post(f"/api/documents/{paper['id']}/summarize", headers=headers)
        if summary.status_code != 200 or not summary.json().get("one_sentence"):
            failures.append("Summary failed")
        else:
            print("\nPaper summary:", summary.json()["one_sentence"][:160])

        handbook = next(document for document in documents if document["title"] == "Employee Handbook")
        university = next(document for document in documents if "University" in document["title"])
        compared = client.post(
            "/api/compare",
            headers=headers,
            json={
                "document_ids": [university["id"], handbook["id"]],
                "user_question": "What is the attendance requirement?",
            },
        )
        if compared.status_code != 200:
            failures.append(f"Compare failed: {compared.text}")
        else:
            print("\nCompare status:", compared.json()["answer_status"])

    if failures:
        print(f"\n{len(failures)} failure(s)")
        for failure in failures:
            print(" -", failure)
        raise SystemExit(1)
    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
