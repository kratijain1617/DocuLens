import re

from app.config import CATEGORY_QUESTIONS, NOT_FOUND_MESSAGE, SYSTEM_INSTRUCTION
from app.pipeline import DATE_RE, compact, stems, tokenize
from app.store import STOPWORDS, content_terms, term_recall

NUMBER_RE = re.compile(r"\$\d[\d,]*|\b\d+(?:\.\d+)?\s*percent\b|\b\d{1,2}:\d{2}\s*[ap]\.m\.", re.I)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
CONDITION_RE = re.compile(r"\b(if|unless|except|provided|does not apply|do not apply|does not cover)\b", re.I)
ACTION_RE = re.compile(r"\b(must|shall|required|need to)\b", re.I)
DEFINITION_RE = re.compile(r"\b(means|is defined as)\b", re.I)
RISK_RE = re.compile(r"\b(warning|prohibited|not permitted|does not cover|probation|penalty|late fee|do not)\b", re.I)


def split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT.split(text.strip())
    return [part.strip() for part in parts if len(part.strip()) > 1]


def _dates(text: str) -> set[str]:
    return {match.group(0) for match in DATE_RE.finditer(text)}


def _follow_ups(category: str, question: str) -> list[str]:
    pool = CATEGORY_QUESTIONS.get(category) or CATEGORY_QUESTIONS["Other"]
    current = set(content_terms(question))
    ranked = []
    for suggestion in pool:
        overlap = len(current & set(content_terms(suggestion)))
        if overlap >= max(1, len(current)):
            continue
        ranked.append(suggestion)
    if len(ranked) < 3:
        for suggestion in pool:
            if suggestion not in ranked and suggestion.lower() not in question.lower():
                ranked.append(suggestion)
    return ranked[:3]


def _related(chunks: list[dict], used_ids: set[str]) -> list[dict]:
    seen = set()
    related = []
    for chunk in chunks:
        key = (chunk["document_name"], chunk["page_number"], chunk["section"])
        if key in seen:
            continue
        seen.add(key)
        related.append(
            {
                "document_name": chunk["document_name"],
                "document_id": chunk["document_id"],
                "page_number": chunk["page_number"],
                "section": chunk["section"],
            }
        )
    return related[:4]


def _citation(chunk: dict, quote: str) -> dict:
    return {
        "document_id": chunk["document_id"],
        "document_name": chunk["document_name"],
        "page_number": chunk["page_number"],
        "section": chunk["section"],
        "quoted_text": quote.strip(),
        "relevance_score": round(float(chunk.get("score") or 0), 2),
    }


def _valid_quote(quote: str, chunk: dict) -> bool:
    return len(compact(quote)) >= 12 and compact(quote) in compact(chunk["text"])


def _conditions(chunks: list[dict], primary: str) -> list[str]:
    found = []
    primary_compact = compact(primary)
    for chunk in chunks:
        for sentence in split_sentences(chunk["text"]):
            if compact(sentence) == primary_compact:
                continue
            if CONDITION_RE.search(sentence) and sentence not in found:
                found.append(sentence)
    return found[:3]


def _confidence(status: str, coverage: float, score: float) -> float:
    if status == "not_found":
        return round(min(0.24, 0.08 + 0.15 * score), 2)
    if status == "conflicting_information":
        return round(min(0.62, 0.46 + 0.12 * score), 2)
    if status == "partially_supported":
        return round(min(0.74, 0.4 + 0.28 * coverage + 0.12 * score), 2)
    return round(min(0.97, 0.5 + 0.28 * coverage + 0.2 * score), 2)


def _pack(question: str, answer: str, status: str, citations: list[dict], chunks: list[dict], category: str, coverage: float, score: float, explanation: str, conditions: list[str] | None = None, follow_ups: list[str] | None = None) -> dict:
    used = {item["quoted_text"] for item in citations}
    related = _related(chunks, used)
    return {
        "answer": answer,
        "explanation": explanation,
        "confidence": _confidence(status, coverage, score),
        "answer_status": status,
        "citations": citations,
        "important_conditions": conditions if conditions is not None else [],
        "related_sections": related,
        "follow_up_questions": follow_ups if follow_ups is not None else _follow_ups(category, question),
        "system_instruction": SYSTEM_INSTRUCTION,
    }


def _not_found(question: str, chunks: list[dict], category: str, score: float = 0.1) -> dict:
    return _pack(
        question,
        NOT_FOUND_MESSAGE,
        "not_found",
        [],
        chunks,
        category,
        0,
        score,
        "The retrieved passages do not state an answer to this question.",
    )


def _list_request(question: str) -> bool:
    lowered = question.lower()
    return bool(re.search(r"\b(what are|what were|list)\b", lowered)) or any(
        word in lowered for word in ("warnings", "findings", "limitations", "requirements", "documents are")
    )


def _best_sentence(question: str, chunk: dict) -> str:
    terms = content_terms(question)
    options = split_sentences(chunk["text"]) or [chunk["text"].strip()]
    options.sort(key=lambda sentence: term_recall(terms, sentence), reverse=True)
    return options[0]


def _competing_dates(question: str, chunks: list[dict]) -> list[tuple[dict, str]]:
    terms = content_terms(question)
    if len(terms) < 2:
        return []
    matches = []
    for chunk in chunks:
        for sentence in split_sentences(chunk["text"]):
            recall = term_recall(terms, f"{chunk['section']} {sentence}")
            dates = _dates(sentence)
            if dates and recall >= 0.67:
                matches.append((chunk, sentence, dates, recall))
    unique_dates = set()
    for _, _, dates, _ in matches:
        unique_dates.update(dates)
    if len(unique_dates) < 2 or len(matches) < 2:
        return []
    chosen = []
    seen_dates = set()
    for chunk, sentence, dates, _ in matches:
        fresh = dates - seen_dates
        if not fresh:
            continue
        seen_dates.update(dates)
        chosen.append((chunk, sentence))
    return chosen if len(seen_dates) >= 2 else []


def _intent_answer(question: str, chunks: list[dict], category: str, selected_page: int | None) -> dict | None:
    lowered = question.lower().strip()
    if re.search(r"not mentioned|not in the (agreement|document|documents|policy|manual|handbook)|something that is not", lowered):
        return _not_found(question, chunks[:3], category, 0.12)

    if re.search(r"what is this (document|paper|manual|agreement|handbook|policy) about|summarize this|what is this about", lowered):
        if not chunks:
            return _not_found(question, [], category)
        ordered = sorted(chunks, key=lambda item: (item["page_number"], item["start_position"]))
        chunk = ordered[0]
        sentence = split_sentences(chunk["text"])[0]
        citation = _citation(chunk, sentence)
        return _pack(
            question,
            sentence,
            "supported",
            [citation],
            [chunk],
            category,
            1,
            max(chunk.get("score") or 0.6, 0.6),
            f'This opening passage is in "{chunk["section"]}" on page {chunk["page_number"]}.',
        )

    if re.search(r"what (do i|should i) need to do|what actions are required|what do i need to do", lowered):
        actions = []
        citations = []
        for chunk in sorted(chunks, key=lambda item: item["page_number"]):
            for sentence in split_sentences(chunk["text"]):
                if ACTION_RE.search(sentence):
                    actions.append(sentence)
                    citations.append(_citation(chunk, sentence))
        if not actions:
            return _not_found(question, chunks, category)
        return _pack(
            question,
            " ".join(actions[:4]),
            "supported",
            citations[:4],
            chunks,
            category,
            1,
            0.7,
            "These sentences use mandatory wording in the retrieved pages.",
        )

    if re.search(r"important deadlines|what are the deadlines|which deadlines", lowered):
        dated = []
        citations = []
        for chunk in chunks:
            for sentence in split_sentences(chunk["text"]):
                if _dates(sentence):
                    dated.append(sentence)
                    citations.append(_citation(chunk, sentence))
        if not dated:
            return _not_found(question, chunks, category)
        status = "conflicting_information" if len({next(iter(_dates(item))) for item in dated if _dates(item)}) > 1 and "deadline" in lowered else "supported"
        if len({date for sentence in dated for date in _dates(sentence)}) > 1 and any("deadline" in sentence.lower() for sentence in dated):
            # Keep a single coherent deadline list unless the same deadline label disagrees.
            status = "supported"
            conflict = _competing_dates(question + " deadline", chunks)
            if len(conflict) >= 2:
                status = "conflicting_information"
        return _pack(
            question,
            " ".join(dated[:4]),
            status,
            citations[:4],
            chunks,
            category,
            1,
            0.72,
            "Each date below is copied from a retrieved passage.",
        )

    if re.search(r"what are the exceptions|exceptions\b", lowered):
        conditions = []
        citations = []
        for chunk in chunks:
            for sentence in split_sentences(chunk["text"]):
                if CONDITION_RE.search(sentence):
                    conditions.append(sentence)
                    citations.append(_citation(chunk, sentence))
        if not conditions:
            return _not_found(question, chunks, category)
        return _pack(
            question,
            conditions[0],
            "supported" if len(conditions) == 1 else "partially_supported",
            citations[:3],
            chunks,
            category,
            0.8,
            0.66,
            "These exception sentences were retrieved from the selected document.",
            conditions=conditions[:3],
        )

    if re.search(r"explain this section|simple words|plain language", lowered):
        pool = [chunk for chunk in chunks if selected_page and chunk["page_number"] == selected_page] or chunks[:1]
        if not pool:
            return _not_found(question, chunks, category)
        chunk = pool[0]
        sentence = split_sentences(chunk["text"])[0]
        return _pack(
            question,
            sentence,
            "supported",
            [_citation(chunk, sentence)],
            [chunk],
            category,
            1,
            0.8,
            f'In the words of the "{chunk["section"]}" section on page {chunk["page_number"]}.',
        )

    if re.search(r"information is missing|what is missing|what information is missing", lowered):
        return None

    if re.search(r"conflicting statements|conflicting information|are there conflicts", lowered):
        conflict = _competing_dates("deadline date", chunks)
        if len(conflict) >= 2:
            citations = [_citation(chunk, sentence) for chunk, sentence in conflict]
            answer = " ".join(sentence for _, sentence in conflict)
            return _pack(
                question,
                answer,
                "conflicting_information",
                citations,
                chunks,
                category,
                1,
                0.7,
                "These retrieved passages give different dates.",
            )
        return _pack(
            question,
            "I did not find two retrieved passages that state different dates for the same requirement.",
            "partially_supported",
            [],
            chunks,
            category,
            0.5,
            0.4,
            "The conflict check compared dates across retrieved passages.",
        )

    if re.search(r"which page", lowered):
        if not chunks:
            return _not_found(question, [], category)
        chunk = chunks[0]
        if chunk["recall"] < 0.34 and chunk["score"] < 0.28:
            return _not_found(question, chunks, category, chunk["score"])
        sentence = _best_sentence(question, chunk)
        return _pack(
            question,
            f'This topic is discussed on page {chunk["page_number"]} in the "{chunk["section"]}" section.',
            "supported",
            [_citation(chunk, sentence)],
            [chunk],
            category,
            chunk["recall"],
            chunk["score"],
            "The page number comes from the highest-ranked retrieved passage.",
        )
    return None


def answer_question(question: str, chunks: list[dict], category: str = "Other", selected_page: int | None = None) -> dict:
    category = category or "Other"
    if not chunks:
        return _not_found(question, [], category, 0)

    intent = _intent_answer(question, chunks, category, selected_page)
    if intent is not None:
        return intent

    terms = content_terms(question)
    best = max(chunks, key=lambda chunk: (chunk["recall"], chunk["score"]))
    if not terms or best["recall"] < 0.5:
        return _not_found(question, chunks, category, best["score"])

    conflict = _competing_dates(question, chunks)
    if len(conflict) >= 2:
        citations = []
        sentences = []
        for chunk, sentence in conflict:
            if _valid_quote(sentence, chunk):
                citations.append(_citation(chunk, sentence))
                sentences.append(sentence)
        if len(citations) >= 2:
            return _pack(
                question,
                " ".join(sentences),
                "conflicting_information",
                citations,
                chunks,
                category,
                1,
                best["score"],
                "Retrieved passages state different dates for this question, so both are shown.",
                conditions=_conditions([item[0] for item in conflict], sentences[0]),
            )

    covered = set()
    chosen: list[tuple[dict, str]] = []
    candidates = []
    for chunk in chunks:
        if chunk["recall"] < 0.34 and chunk["score"] < 0.25:
            continue
        for sentence in split_sentences(chunk["text"]):
            gain = [term for term in terms if term in set(stems(sentence))]
            candidates.append((len(gain), chunk.get("score", 0), chunk, sentence, gain))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    if _list_request(question):
        top_chunk = chunks[0]
        if term_recall(terms, top_chunk["section"]) >= 0.5 or top_chunk["recall"] >= 0.5:
            for sentence in split_sentences(top_chunk["text"])[:4]:
                chosen.append((top_chunk, sentence))
                covered.update(stems(sentence))

    if not chosen:
        for _, _, chunk, sentence, gain in candidates:
            new_terms = [term for term in gain if term not in covered]
            if not new_terms and chosen:
                continue
            if not gain:
                continue
            chosen.append((chunk, sentence))
            covered.update(new_terms)
            if set(terms).issubset(covered):
                break

    if not chosen:
        return _not_found(question, chunks, category, best["score"])

    coverage = len(set(terms) & covered) / len(terms)
    if _list_request(question) and chosen:
        coverage = max(coverage, term_recall(terms, f"{chunks[0]['section']} {chunks[0]['text']}"))
    citations = []
    answer_parts = []
    for chunk, sentence in chosen:
        if not _valid_quote(sentence, chunk):
            continue
        answer_parts.append(sentence)
        citations.append(_citation(chunk, sentence))
    if not citations:
        return _not_found(question, chunks, category, best["score"])

    status = "supported" if coverage >= 0.67 else "partially_supported"
    primary = answer_parts[0]
    explanation = (
        f'The wording above is quoted from "{citations[0]["section"]}" on page {citations[0]["page_number"]} '
        f'of {citations[0]["document_name"]}.'
    )
    return _pack(
        question,
        " ".join(answer_parts),
        status,
        citations,
        chunks,
        category,
        coverage,
        best["score"],
        explanation,
        conditions=_conditions([chunk for chunk, _ in chosen], primary),
    )


def validate_citations(result: dict, chunks: list[dict]) -> dict:
    by_page = {}
    for chunk in chunks:
        by_page.setdefault((chunk["document_id"], chunk["page_number"]), []).append(chunk)
    kept = []
    for citation in result.get("citations", []):
        pool = by_page.get((citation["document_id"], citation["page_number"]), [])
        if any(compact(citation["quoted_text"]) in compact(chunk["text"]) for chunk in pool):
            kept.append(citation)
    result["citations"] = kept
    if result["answer_status"] in {"supported", "partially_supported", "conflicting_information"} and not kept:
        return _not_found(result.get("question", ""), chunks, "Other", result.get("confidence", 0.1))
    return result


def compare_documents(question: str, groups: list[tuple[dict, list[dict]]]) -> dict:
    columns = []
    for document, retrieved in groups:
        result = answer_question(question, retrieved, document["category"])
        result = validate_citations(result, retrieved)
        columns.append(
            {
                "document_id": document["id"],
                "document_name": document["file_name"],
                "title": document["title"],
                "category": document["category"],
                "summary": result["answer"],
                "answer_status": result["answer_status"],
                "confidence": result["confidence"],
                "citations": result["citations"],
                "important_conditions": result["important_conditions"],
            }
        )

    similarities = _shared_points(columns)
    conflicts = []
    differences = []
    for column in columns:
        differences.append(
            {
                "text": column["summary"],
                "citations": column["citations"],
                "document_name": column["document_name"],
            }
        )
        if column["answer_status"] == "conflicting_information":
            conflicts.append(
                {
                    "text": column["summary"],
                    "citations": column["citations"],
                    "document_name": column["document_name"],
                }
            )

    statuses = {column["answer_status"] for column in columns}
    if conflicts or "conflicting_information" in statuses:
        status = "conflicting_information"
    elif statuses <= {"not_found"}:
        status = "not_found"
    elif "not_found" in statuses or "partially_supported" in statuses:
        status = "partially_supported"
    else:
        status = "supported"
    confidence = round(sum(column["confidence"] for column in columns) / max(1, len(columns)), 2)
    summary = "Each column quotes only passages retrieved from that document."
    if status == "not_found":
        summary = NOT_FOUND_MESSAGE
    elif status == "conflicting_information":
        summary = "At least one selected document contains retrieved passages that do not agree."
    return {
        "question": question,
        "answer": summary,
        "answer_status": status,
        "confidence": confidence,
        "summary": summary,
        "similarities": similarities,
        "differences": differences,
        "conflicts": conflicts,
        "documents": columns,
        "follow_up_questions": _follow_ups(columns[0]["category"] if columns else "Other", question),
    }


def _shared_points(columns: list[dict]) -> list[dict]:
    phrase_map: list[set[str]] = []
    for column in columns:
        text = " ".join(citation["quoted_text"] for citation in column["citations"])
        tokens = [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2]
        grams = {f"{tokens[index]} {tokens[index + 1]}" for index in range(len(tokens) - 1)}
        phrase_map.append(grams)
    if not phrase_map:
        return []
    shared = set.intersection(*phrase_map) if phrase_map else set()
    points = []
    for phrase in sorted(shared, key=len, reverse=True):
        citations = []
        for column in columns:
            for citation in column["citations"]:
                if phrase in citation["quoted_text"].lower() and citation not in citations:
                    citations.append(citation)
                    break
        if len(citations) >= 2:
            points.append({"text": f'Shared phrase: "{phrase}".', "citations": citations})
        if len(points) == 3:
            break
    return points


def summarize_document(document: dict, chunks: list[dict]) -> dict:
    from app.pipeline import MISSING_TOPICS

    ordered = sorted(chunks, key=lambda item: (item["page_number"], item["start_position"]))
    topics = []
    dates = []
    numbers = []
    actions = []
    definitions = []
    risks = []
    lead = ""
    detailed_parts = []
    seen_sections = set()
    all_citations = []

    def add(bucket: list, chunk: dict, sentence: str):
        if any(item["text"] == sentence for item in bucket):
            return
        citation = _citation(chunk, sentence)
        bucket.append({"text": sentence, "citation": citation})
        all_citations.append(citation)

    for chunk in ordered:
        if chunk["section"] not in seen_sections:
            seen_sections.add(chunk["section"])
            topics.append(chunk["section"])
            first = split_sentences(chunk["text"])
            if first:
                detailed_parts.append(first[0])
                if not lead:
                    lead = first[0]
                    all_citations.append(_citation(chunk, first[0]))
        for sentence in split_sentences(chunk["text"]):
            if _dates(sentence):
                add(dates, chunk, sentence)
            if NUMBER_RE.search(sentence) or "$" in sentence:
                add(numbers, chunk, sentence)
            if ACTION_RE.search(sentence):
                add(actions, chunk, sentence)
            if DEFINITION_RE.search(sentence):
                add(definitions, chunk, sentence)
            if RISK_RE.search(sentence):
                add(risks, chunk, sentence)

    full = "\n".join(chunk["text"] for chunk in ordered).lower()
    missing = [topic for topic in MISSING_TOPICS.get(document["category"], []) if topic not in full]
    unique_citations = []
    seen = set()
    for citation in all_citations:
        key = (citation["page_number"], citation["quoted_text"])
        if key in seen:
            continue
        seen.add(key)
        unique_citations.append(citation)

    return {
        "document_id": document["id"],
        "document_name": document["file_name"],
        "title": document["title"],
        "category": document["category"],
        "one_sentence": lead,
        "detailed": " ".join(detailed_parts[:6]),
        "topics": topics,
        "important_dates": dates[:6],
        "important_numbers": numbers[:6],
        "required_actions": actions[:6],
        "definitions": definitions[:4],
        "risks_or_warnings": risks[:6],
        "missing_information": missing,
        "suggested_questions": CATEGORY_QUESTIONS.get(document["category"], CATEGORY_QUESTIONS["Other"]),
        "citations": unique_citations[:12],
        "answer_status": "supported" if lead else "not_found",
    }


def llm_answer(question: str, chunks: list[dict], history: list[dict], category: str) -> dict | None:
    import os

    import httpx

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or not chunks:
        return None
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    context = [
        {
            "document_name": chunk["document_name"],
            "page_number": chunk["page_number"],
            "section": chunk["section"],
            "text": chunk["text"],
        }
        for chunk in chunks
    ]
    prompt = {
        "question": question,
        "document_category": category,
        "conversation_history": history[-6:],
        "context": context,
        "required_shape": {
            "answer": "",
            "explanation": "",
            "confidence": 0,
            "answer_status": "supported|partially_supported|conflicting_information|not_found",
            "citations": [
                {
                    "document_name": "",
                    "page_number": 0,
                    "section": "",
                    "quoted_text": "",
                    "relevance_score": 0,
                }
            ],
            "important_conditions": [],
            "related_sections": [],
            "follow_up_questions": [],
        },
    }
    try:
        response = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION + " Return JSON only. Every quoted_text must be copied exactly from context. Do not cite a page that is not in context."},
                    {"role": "user", "content": __import__("json").dumps(prompt)},
                ],
            },
            timeout=40,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = __import__("json").loads(content)
    except Exception:
        return None

    name_to_chunk = {}
    for chunk in chunks:
        name_to_chunk.setdefault((chunk["document_name"], chunk["page_number"]), []).append(chunk)
    citations = []
    for raw in parsed.get("citations") or []:
        pool = name_to_chunk.get((raw.get("document_name"), raw.get("page_number")), [])
        quote = (raw.get("quoted_text") or "").strip()
        match = next((chunk for chunk in pool if quote and compact(quote) in compact(chunk["text"])), None)
        if match is None:
            continue
        citations.append(_citation(match, quote))
    status = parsed.get("answer_status") or "not_found"
    if status not in {"supported", "partially_supported", "conflicting_information", "not_found"}:
        status = "not_found"
    if status != "not_found" and not citations:
        return None
    if status == "not_found":
        answer = NOT_FOUND_MESSAGE
    else:
        answer = (parsed.get("answer") or "").strip()
        if not answer:
            return None
    return {
        "answer": answer,
        "explanation": (parsed.get("explanation") or "").strip(),
        "confidence": float(parsed.get("confidence") or 0.5),
        "answer_status": status,
        "citations": citations,
        "important_conditions": [str(item) for item in (parsed.get("important_conditions") or [])][:4],
        "related_sections": _related(chunks, set()),
        "follow_up_questions": [str(item) for item in (parsed.get("follow_up_questions") or [])][:3] or _follow_ups(category, question),
        "system_instruction": SYSTEM_INSTRUCTION,
    }


def answer_with_optional_llm(question: str, chunks: list[dict], category: str, history: list[dict] | None = None, selected_page: int | None = None) -> dict:
    grounded = answer_question(question, chunks, category, selected_page)
    grounded = validate_citations(grounded, chunks)
    model = llm_answer(question, chunks, history or [], category)
    if not model:
        return grounded
    model = validate_citations({**model, "question": question}, chunks)
    if model["answer_status"] == "not_found" and grounded["answer_status"] == "supported" and grounded["confidence"] >= 0.75:
        return grounded
    if model["answer_status"] != "not_found" and not model["citations"]:
        return grounded
    return model


def expand_question(question: str, history: list[dict] | None) -> str:
    if not history:
        return question
    lowered = question.lower().strip()
    terms = content_terms(question)
    standalone = bool(
        re.search(
            r"what is this (document|paper|manual|agreement|handbook|policy) about|summarize this",
            lowered,
        )
    )
    anaphora = lowered.startswith("what about") or bool(re.search(r"\b(that|those|it|same)\b", lowered))
    if standalone or (len(terms) >= 2 and not anaphora):
        return question
    previous = ""
    for item in reversed(history):
        if item.get("role") == "user" and item.get("content"):
            previous = item["content"]
            break
    if previous and previous.lower() not in question.lower():
        return f"{question} {previous}"
    return question
