import re

from app.services.topic_cleaner import ADMIN_PHRASES, clean_topic
from app.services.topic_normalizer import CANONICAL_SYNONYMS, canonicalize_topic

# Canonical academic concepts we always trust after cleaning.
KNOWN_ACADEMIC_CONCEPTS = set(CANONICAL_SYNONYMS.keys())

# Bloom taxonomy levels are exam-design metadata, not topics.
BLOOM_LEVELS = {
    "remember",
    "remember knowledge",
    "understand",
    "apply",
    "analyze",
    "analyse",
    "evaluate",
    "create",
}

# Words that strongly suggest administrative/document text.
ADMIN_ROOT_WORDS = {
    "enroll",
    "enrolment",
    "enrollment",
    "attempt",
    "semester",
    "branch",
    "dean",
    "principal",
    "hod",
    "faculty",
    "digitally",
    "signed",
    "teaching",
    "scheme",
    "outcome",
    "outcomes",
    "bloom",
    "taxonomy",
    "bachelor",
    "technology",
    "engineering",
    "university",
    "institute",
    "college",
    "session",
    "academic",
    "assumption",
    "assumptions",
    "necessary",
    "instructions",
    "instruction",
    "code",
    "credits",
    "hours",
    "tutorial",
    "examination",
    "examinations",
}

ADMIN_SUBSTRING_PHRASES = [
    "enroll no",
    "attempt all questions",
    "remember knowledge",
    "bloom taxonomy",
    "chart graph",
    "co no",
    "course code",
    "course outcome",
    "teaching scheme",
    "dean principal",
    "digitally signed",
    "exam instructions",
    "make suitable assumptions",
    "academic session",
    "question paper",
    "bachelor of technology",
    "sem ii",
    "semester ii",
    "branch ce",
    "computer engineering",
    "artificial intelligence machine learning",
    "artificial intelligence",
    "machine learning",
]

ROLE_NAME_PATTERN = re.compile(
    r"\b(dr|prof|professor|mr|mrs|ms)\.?\s+[a-z]{3,}\b",
    re.IGNORECASE,
)
SEMESTER_PATTERN = re.compile(r"\bsem(ester)?\s*(i{1,3}|iv|v|vi|[0-9]+)\b", re.IGNORECASE)
BRANCH_PATTERN = re.compile(r"\bbranch\s+[a-z]{2,}\b", re.IGNORECASE)
MOSTLY_NUMBERS_PATTERN = re.compile(r"^[0-9\s\.\-]+$")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def is_valid_academic_topic(topic: str) -> bool:
    """
    Stage 7.6 topic validation gate.
    A topic survives only if it looks like a real academic concept.
    """
    cleaned = clean_topic(topic)
    if not cleaned:
        return False

    normalized = _normalize(cleaned)
    canonical = canonicalize_topic(cleaned)

    # Rule 1: Known canonical concepts are always accepted.
    if canonical in KNOWN_ACADEMIC_CONCEPTS:
        return True

    # Rule 2: Bloom levels and taxonomy labels are never topics.
    if normalized in BLOOM_LEVELS:
        return False
    if "bloom" in normalized and "taxonomy" in normalized:
        return False

    # Rule 3: Exact admin phrases are never topics.
    if normalized in ADMIN_PHRASES:
        return False

    # Rule 4: Admin substrings indicate document metadata.
    for phrase in ADMIN_SUBSTRING_PHRASES:
        if phrase in normalized:
            return False

    # Rule 5: Person/role lines are never topics.
    if ROLE_NAME_PATTERN.search(normalized):
        return False

    # Rule 6: Semester/branch lines are never topics.
    if SEMESTER_PATTERN.search(normalized):
        return False
    if BRANCH_PATTERN.search(normalized):
        return False

    # Rule 7: Numeric-only fragments are never topics.
    if MOSTLY_NUMBERS_PATTERN.match(normalized):
        return False

  # Rule 8: Very short fragments are unlikely to be concepts.
    words = normalized.split()
    if len(words) < 2 and normalized not in {"eigenvalues", "determinants", "orthogonality"}:
        return False

    # Rule 9: If most words are administrative roots, reject.
    admin_word_count = sum(1 for word in words if word in ADMIN_ROOT_WORDS)
    if admin_word_count >= max(1, len(words) // 2):
        return False

    # Rule 10: Accept multi-word phrases with at least one non-admin word.
    if len(words) >= 2:
        return True

    return False


def filter_valid_topics(topics: list[str]) -> list[str]:
    return [topic for topic in topics if is_valid_academic_topic(topic)]
