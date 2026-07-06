import re

from app.services.heading_detector import extract_headings
from app.services.topic_cleaner import clean_topic, is_academic_stopword

# Known multi-word academic concepts (longest match wins).
ACADEMIC_CONCEPTS: list[str] = [
    "inner product space",
    "reduced row echelon form",
    "row echelon form",
    "orthogonal projection",
    "characteristic polynomial",
    "gram schmidt process",
    "linear transformation",
    "linear independence",
    "orthogonal basis",
    "matrix multiplication",
    "gaussian elimination",
    "vector space",
    "inner product",
    "linear systems",
    "system of linear equations",
    "linear equations",
    "eigenvalues",
    "eigenvectors",
    "cramer rule",
    "matrix rank",
    "basis and dimension",
    "lu decomposition",
    "fourier series",
    "laplace transform",
    "differential equations",
]

# Sort longest first so we do not split concepts incorrectly.
ACADEMIC_CONCEPTS.sort(key=len, reverse=True)

DEFINITION_PATTERN = re.compile(
    r"\b(definition|theorem|lemma|corollary|remark)\s*(of|on)?\s+([a-z][a-z\s\-]{3,60})",
    re.IGNORECASE,
)
CAPITALIZED_PHRASE_PATTERN = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\b"
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def _normalize_lookup(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _find_known_concepts(text: str) -> list[str]:
    lowered = _normalize_lookup(text)
    found: list[str] = []
    used_spans: list[tuple[int, int]] = []

    for concept in ACADEMIC_CONCEPTS:
        start = 0
        while True:
            index = lowered.find(concept, start)
            if index == -1:
                break

            end = index + len(concept)
            overlaps = any(not (end <= s or index >= e) for s, e in used_spans)
            if not overlaps:
                found.append(concept)
                used_spans.append((index, end))
            start = index + 1

    return found


def _extract_definition_phrases(sentence: str) -> list[str]:
    phrases: list[str] = []
    for match in DEFINITION_PATTERN.finditer(sentence):
        phrase = match.group(3).strip(" .,:;")
        cleaned = clean_topic(phrase)
        if cleaned:
            phrases.append(cleaned)
    return phrases


def _extract_capitalized_phrases(sentence: str) -> list[str]:
    phrases: list[str] = []
    for match in CAPITALIZED_PHRASE_PATTERN.finditer(sentence):
        phrase = match.group(1).strip()
        words = phrase.split()
        if len(words) < 2:
            continue
        if any(is_academic_stopword(word.lower()) for word in (words[0], words[-1])):
            continue
        cleaned = clean_topic(phrase.lower())
        if cleaned:
            phrases.append(cleaned)
    return phrases


def _split_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT_PATTERN.split(text.replace("\n", " "))
    return [part.strip() for part in parts if part.strip()]


def generate_topic_candidates(text: str) -> list[dict]:
    """
  Generate topic candidates with source metadata.
  Returns dictionaries like:
  {"text": "vector space", "source": "heading", "boost": 0.4}
    """
    candidates: list[dict] = []

    for heading, confidence in extract_headings(text):
        cleaned = clean_topic(heading.lower())
        if cleaned:
            candidates.append(
                {
                    "text": cleaned,
                    "source": "heading",
                    "boost": 0.25 + confidence,
                }
            )

    for concept in _find_known_concepts(text):
        candidates.append(
            {
                "text": concept,
                "source": "known_concept",
                "boost": 0.45,
            }
        )

    for sentence in _split_sentences(text):
        for phrase in _extract_definition_phrases(sentence):
            candidates.append(
                {
                    "text": phrase,
                    "source": "definition",
                    "boost": 0.35,
                }
            )

        for phrase in _extract_capitalized_phrases(sentence):
            candidates.append(
                {
                    "text": phrase,
                    "source": "capitalized_phrase",
                    "boost": 0.20,
                }
            )

        for concept in _find_known_concepts(sentence):
            candidates.append(
                {
                    "text": concept,
                    "source": "sentence_concept",
                    "boost": 0.30,
                }
            )

    return candidates
