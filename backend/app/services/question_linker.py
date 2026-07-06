import re
from collections import Counter, defaultdict

from app.services.question_pattern_engine import (
    _detect_patterns_from_question,
    _split_into_question_candidates,
)
from app.services.topic_engine import extract_candidate_topics

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
MARKS_PATTERN = re.compile(r"\((\d+)\s*marks?\)|\b(\d+)\s*marks?\b", re.IGNORECASE)


def _extract_year_from_filename(filename: str) -> str | None:
    match = YEAR_PATTERN.search(filename)
    return match.group(0) if match else None


def _extract_marks_from_question(question_text: str) -> int | None:
    match = MARKS_PATTERN.search(question_text.lower())
    if not match:
        return None
    value = match.group(1) or match.group(2)
    return int(value) if value else None


def build_topic_question_links(
    documents: list[dict[str, str]],
) -> dict[str, dict]:
    """
    Link canonical topics to question styles, marks, and years.
    Reuses question pattern detection rules from Stage 5.
    """
    pattern_counter: dict[str, Counter[str]] = defaultdict(Counter)
    marks_counter: dict[str, list[int]] = defaultdict(list)
    years_counter: dict[str, set[str]] = defaultdict(set)
    year_hits_counter: dict[str, Counter[str]] = defaultdict(Counter)
    paper_files: dict[str, set[str]] = defaultdict(set)

    for document in documents:
        if document["file_type"] != "question_paper":
            continue

        filename = document["filename"]
        year = _extract_year_from_filename(filename)
        text = document["text"]
        if not text.strip():
            continue

        for question in _split_into_question_candidates(text):
            patterns = _detect_patterns_from_question(question)
            if not patterns:
                continue

            marks = _extract_marks_from_question(question)
            raw_topics = extract_candidate_topics(question, file_type="question_paper")
            canonical_topics = set(raw_topics)

            for topic in canonical_topics:
                paper_files[topic].add(filename)
                if year:
                    years_counter[topic].add(year)
                    year_hits_counter[topic][year] += 1
                if marks is not None:
                    marks_counter[topic].append(marks)
                for pattern in patterns:
                    pattern_counter[topic][pattern] += 1

    topic_links: dict[str, dict] = {}
    for topic, counter in pattern_counter.items():
        question_types = [name for name, _ in counter.most_common(3)]
        marks_values = marks_counter.get(topic, [])
        average_marks = (
            round(sum(marks_values) / len(marks_values), 1) if marks_values else None
        )
        highest_marks = max(marks_values) if marks_values else None
        years = sorted(years_counter.get(topic, set()))
        topic_links[topic] = {
            "questionTypes": question_types,
            "averageMarks": average_marks,
            "highestMarks": highest_marks,
            "yearsAppeared": years,
            "yearCounts": dict(year_hits_counter.get(topic, {})),
            "questionPaperCount": len(paper_files.get(topic, set())),
        }

    return topic_links


def summarize_pattern_links(topic_links: dict[str, dict]) -> dict[str, list[str]]:
    """Pattern name -> top canonical topics asked in that style."""
    pattern_to_topics: dict[str, Counter[str]] = defaultdict(Counter)

    for topic, details in topic_links.items():
        for pattern in details.get("questionTypes", []):
            pattern_to_topics[pattern][topic] += 1

    return {
        pattern: [topic for topic, _ in counter.most_common(5)]
        for pattern, counter in pattern_to_topics.items()
    }
