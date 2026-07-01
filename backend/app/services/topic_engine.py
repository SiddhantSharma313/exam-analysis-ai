import re
from collections import Counter, defaultdict


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "using",
    "use",
    "this",
    "these",
    "those",
    "your",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_file_type(filename: str) -> str:
    name = filename.lower()
    if "syllabus" in name:
        return "syllabus"
    if "assignment" in name:
        return "assignment"
    if "lab" in name or "manual" in name:
        return "lab_manual"
    if "question" in name or "paper" in name or "exam" in name:
        return "question_paper"
    return "other"


def _extract_heading_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Keep short heading-like lines (common in syllabus and questions).
        if len(line) > 90:
            continue

        cleaned_line = re.sub(r"^[0-9\-\.\)\(]+\s*", "", line)
        cleaned_line = re.sub(r"[^A-Za-z0-9\s]", " ", cleaned_line)
        words = [w for w in cleaned_line.lower().split() if w not in STOPWORDS]
        if 2 <= len(words) <= 6:
            candidates.append(" ".join(words))
    return candidates


def _extract_phrase_candidates(text: str) -> list[str]:
    normalized = _normalize_text(text)
    words = re.findall(r"[a-z]{3,}", normalized)
    filtered = [w for w in words if w not in STOPWORDS]

    phrases: list[str] = []
    for size in (2, 3):
        for index in range(len(filtered) - size + 1):
            phrase = " ".join(filtered[index : index + size])
            phrases.append(phrase)
    return phrases


def extract_candidate_topics(text: str) -> list[str]:
    heading_candidates = _extract_heading_candidates(text)
    phrase_candidates = _extract_phrase_candidates(text)
    combined = heading_candidates + phrase_candidates
    return [topic for topic in combined if len(topic) >= 6]


def analyze_topics_from_documents(documents: list[dict[str, str]]) -> dict:
    topic_counter: Counter[str] = Counter()
    files_appeared_in: dict[str, set[str]] = defaultdict(set)
    syllabus_topics: set[str] = set()
    asked_topics: set[str] = set()

    for document in documents:
        filename = document["filename"]
        text = document["text"]
        file_type = document["file_type"]

        if not text.strip():
            continue

        document_topics = extract_candidate_topics(text)
        local_counter = Counter(document_topics)

        for topic, count in local_counter.items():
            if count < 2:
                continue
            topic_counter[topic] += count
            files_appeared_in[topic].add(filename)

            if file_type == "syllabus":
                syllabus_topics.add(topic)
            else:
                asked_topics.add(topic)

    detected_topics = sorted(topic_counter.keys(), key=lambda t: topic_counter[t], reverse=True)

    importance_tier = {
        "highlyImportant": [],
        "mediumImportance": [],
        "lowImportance": [],
        "neverAsked": [],
    }

    for topic in detected_topics:
        frequency = topic_counter[topic]
        file_count = len(files_appeared_in[topic])

        if frequency >= 8 or file_count >= 3:
            importance_tier["highlyImportant"].append(topic)
        elif frequency >= 4 or file_count == 2:
            importance_tier["mediumImportance"].append(topic)
        else:
            importance_tier["lowImportance"].append(topic)

    never_asked_topics = sorted(topic for topic in syllabus_topics if topic not in asked_topics)
    importance_tier["neverAsked"] = never_asked_topics

    return {
        "detectedTopics": detected_topics,
        "topicFrequency": dict(topic_counter),
        "filesAppearedIn": {topic: sorted(list(files)) for topic, files in files_appeared_in.items()},
        "importanceTier": importance_tier,
        "neverAskedTopics": never_asked_topics,
    }
