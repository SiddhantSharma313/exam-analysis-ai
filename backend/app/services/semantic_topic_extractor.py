from collections import Counter

from app.services.confidence_engine import (
    EXTRACTION_CONFIDENCE_THRESHOLD,
    compute_topic_confidence,
    passes_extraction_threshold,
)
from app.services.topic_candidate_generator import generate_topic_candidates
from app.services.topic_cleaner import clean_topic
from app.services.topic_normalizer import canonicalize_topic
from app.services.topic_validator import is_valid_academic_topic

UNIVERSE_FILE_TYPES = {"syllabus", "unit_notes", "lecture_notes"}
EXAM_FILE_TYPES = {"question_paper"}


def extract_semantic_topics(
    text: str,
    file_type: str,
) -> list[dict]:
    """
    Extract semantic topics from one document.
    Returns canonical topics with confidence and source signals.
    """
    if not text.strip():
        return []

    raw_candidates = generate_topic_candidates(text)
    local_counter: Counter[str] = Counter()
    signal_map: dict[str, dict] = {}

    for candidate in raw_candidates:
        cleaned = clean_topic(candidate["text"])
        if not cleaned:
            continue

        canonical = canonicalize_topic(cleaned)
        if not is_valid_academic_topic(canonical):
            continue
        local_counter[canonical] += 1

        signals = signal_map.setdefault(
            canonical,
            {
                "from_heading": False,
                "known_concept": False,
                "from_definition": False,
                "in_syllabus_universe": False,
                "in_unit_notes": False,
                "in_lecture_notes": False,
                "in_question_paper": False,
                "repeat_count": 0,
                "file_count": 1,
                "paper_count": 0,
            },
        )

        source = candidate["source"]
        if source == "heading":
            signals["from_heading"] = True
        if source == "known_concept":
            signals["known_concept"] = True
        if source == "definition":
            signals["from_definition"] = True

    results: list[dict] = []
    for topic, repeat_count in local_counter.items():
        signals = signal_map[topic]
        signals["repeat_count"] = repeat_count

        if file_type in UNIVERSE_FILE_TYPES:
            signals["in_syllabus_universe"] = file_type == "syllabus"
            signals["in_unit_notes"] = file_type == "unit_notes"
            signals["in_lecture_notes"] = file_type == "lecture_notes"

        if file_type in EXAM_FILE_TYPES:
            signals["in_question_paper"] = True
            signals["paper_count"] = 1

        confidence = compute_topic_confidence(signals)
        if not passes_extraction_threshold(confidence):
            continue

        results.append(
            {
                "name": topic,
                "confidence": confidence,
                "count": repeat_count,
                "signals": signals,
            }
        )

    return results


def extract_semantic_topic_names(text: str, file_type: str = "other") -> list[str]:
    """Backward-compatible helper used by question pattern modules."""
    return [item["name"] for item in extract_semantic_topics(text, file_type)]
