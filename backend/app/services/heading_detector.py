import re

# Numbered academic section markers.
SECTION_PREFIX_PATTERN = re.compile(
    r"^(unit|chapter|section|module|part)\s*[\divxlc]+[\s:\.\-]*",
    re.IGNORECASE,
)
NUMBERED_HEADING_PATTERN = re.compile(r"^\d+([\.\)]\d+)*[\.\)]\s+\S")


def _word_count(line: str) -> int:
    return len(re.findall(r"[A-Za-z]+", line))


def detect_heading_confidence(line: str) -> float:
    """
    Estimate whether one text line is a heading.
    PyPDF2 does not preserve font size reliably, so we use line patterns.
    """
    stripped = line.strip()
    if not stripped:
        return 0.0

  # Long prose lines are usually paragraphs, not headings.
    if len(stripped) > 100 or _word_count(stripped) > 12:
        return 0.0

    confidence = 0.0
    words = stripped.split()

    if SECTION_PREFIX_PATTERN.match(stripped):
        confidence += 0.35

    if NUMBERED_HEADING_PATTERN.match(stripped):
        confidence += 0.30

    alpha_words = [word for word in words if word.isalpha()]
    if len(alpha_words) >= 2 and all(word.isupper() for word in alpha_words):
        confidence += 0.45

    title_case_words = sum(1 for word in words if word[:1].isupper())
    if len(words) >= 2 and title_case_words >= max(2, len(words) * 0.6):
        confidence += 0.25

    if not stripped.endswith((".", "?", "!")):
        confidence += 0.10

    if len(stripped) <= 55:
        confidence += 0.10

    return min(confidence, 1.0)


def extract_headings(text: str, min_confidence: float = 0.35) -> list[tuple[str, float]]:
    headings: list[tuple[str, float]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        confidence = detect_heading_confidence(line)
        if confidence < min_confidence:
            continue

        cleaned = re.sub(r"^[0-9\-\.\)\(]+\s*", "", line)
        cleaned = SECTION_PREFIX_PATTERN.sub("", cleaned).strip(" :-.")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) >= 4:
            headings.append((cleaned, confidence))

    return headings
