import re

# --- Group 1: Basic grammar stopwords (not concepts by themselves) ---
BASIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "to", "with", "using", "use",
    "this", "these", "those", "your", "we", "you", "our", "their", "its",
}

# --- Group 2: Math discourse words (sentence glue, not topics) ---
DISCOURSE_STOPWORDS = {
    "let", "then", "thus", "therefore", "suppose", "consider", "assume", "given",
    "hence", "where", "when", "which", "such", "each", "every", "all", "any",
    "if", "else", "also", "can", "will", "may", "must", "should", "would",
}

# --- Group 3: Exam instruction verbs (question wording, not topics) ---
INSTRUCTION_STOPWORDS = {
    "show", "prove", "find", "define", "explain", "discuss", "derive", "compute",
    "calculate", "solve", "state", "write", "draw", "list", "describe", "evaluate",
}

# --- Group 4: Exam/document boilerplate ---
DOCUMENT_STOPWORDS = {
    "question", "marks", "mark", "paper", "page", "figure", "example", "solution",
    "answer", "que", "main", "digitally", "signed", "department", "faculty",
    "principal", "course", "credits", "hours", "tutorial", "semester", "university",
    "college", "school", "examination", "exam", "time", "allowed", "maximum",
    "total", "code", "date", "name", "roll", "register", "subject", "enroll",
    "enrollment", "enrolment", "attempt", "dean", "hod", "bloom", "taxonomy",
    "remember", "understand", "apply", "analyze", "analyse", "evaluate", "create",
    "teaching", "scheme", "outcome", "outcomes", "branch", "bachelor", "technology",
    "session", "institute", "assumption", "assumptions", "necessary", "instructions",
}

# --- Group 5: Words common in OCR garbage bigrams (not used as edge stopwords alone) ---
NOISE_BIGRAM_WORDS = {
    "cos", "sin", "tan", "generated", "consisting", "then", "product",
}

ACADEMIC_STOPWORDS = (
    BASIC_STOPWORDS
    | DISCOURSE_STOPWORDS
    | INSTRUCTION_STOPWORDS
    | DOCUMENT_STOPWORDS
)

# Administrative phrases — document metadata, NEVER academic topics.
ADMIN_PHRASES = {
    "question paper",
    "supplementary resources",
    "outcome wise",
    "digitally signed",
    "unit topics",
    "topics contact",
    "course outcomes",
    "program outcomes",
    "marks que",
    "end semester",
    "internal assessment",
    "page no",
    "time allowed",
    "maximum marks",
    "total marks",
    "space inner",
    "vector then",
    "let vectors",
    "product generated",
    "basis consisting",
    "then cos cos",
    "que que",
    "main main",
    "enroll no",
    "attempt all questions",
    "remember knowledge",
    "understand",
    "apply",
    "analyze",
    "analyse",
    "evaluate",
    "create",
    "bloom taxonomy",
    "chart graph of bloom taxonomy",
    "chart graph",
    "co no",
    "sem ii",
    "semester ii",
    "branch ce ai",
    "computer engineering",
    "artificial intelligence machine learning",
    "course code",
    "course outcome",
    "teaching scheme",
    "dean principal",
    "hod",
    "exam instructions",
    "make suitable assumptions wherever necessary",
    "make suitable assumptions",
    "academic session",
    "bachelor of technology",
    "university headers",
    "institute names",
    "branch names",
}

SIGNATURE_PATTERNS = [
    r"\bdr\.?\s+[a-z]+\b",
    r"\bprof\.?\s+[a-z]+\b",
    r"\bprofessor\s+[a-z]+\b",
    r"\bdigitally\s+signed\b",
    r"\bsignature\b",
]

OUTCOME_LABEL_PATTERN = re.compile(
    r"\b(co|po)\s*\d+\b|\b\d+\s*l\d+\s*co\d+\b",
    re.IGNORECASE,
)
DIGIT_CLUSTER_PATTERN = re.compile(r"\b\d{4,}\b")
TIMESTAMP_PATTERN = re.compile(
    r"\b\d{1,2}[:/]\d{1,2}[:/]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b"
)
MARKS_PATTERN = re.compile(r"\b\d+\s*marks?\b|\bmarks?\s*\d+\b", re.IGNORECASE)
NUMBERING_PREFIX_PATTERN = re.compile(r"^[\d\.\)\(\-]+\s*")
HEADER_FOOTER_PATTERNS = [
    r"\bpage\s+\d+\b",
    r"\bconfidential\b",
    r"\bscheme\s+of\s+evaluation\b",
]


def is_academic_stopword(word: str) -> bool:
    return word.lower() in ACADEMIC_STOPWORDS


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _has_repeated_word(topic: str) -> bool:
    words = topic.split()
    if len(words) < 2:
        return False
    return len(set(words)) < len(words)


def _is_mostly_non_alpha(topic: str) -> bool:
    alpha_chars = sum(1 for char in topic if char.isalpha())
    return alpha_chars < max(3, len(topic) * 0.4)


def _has_stopword_edges(topic: str) -> bool:
    words = topic.split()
    if not words:
        return True
    return is_academic_stopword(words[0]) or is_academic_stopword(words[-1])


def _is_noise_bigram(topic: str) -> bool:
    """Reject common OCR bigrams like 'space inner' or 'vector then'."""
    words = topic.split()
    if len(words) != 2:
        return False
    return words[0] in NOISE_BIGRAM_WORDS and words[1] in NOISE_BIGRAM_WORDS


def clean_topic(topic: str) -> str | None:
    if not topic or not topic.strip():
        return None

    cleaned = _normalize_spaces(topic)
    cleaned = NUMBERING_PREFIX_PATTERN.sub("", cleaned).strip()
    cleaned = MARKS_PATTERN.sub("", cleaned).strip()
    cleaned = OUTCOME_LABEL_PATTERN.sub("", cleaned).strip()
    cleaned = DIGIT_CLUSTER_PATTERN.sub("", cleaned).strip()
    cleaned = TIMESTAMP_PATTERN.sub("", cleaned).strip()
    cleaned = _normalize_spaces(cleaned)

    if len(cleaned) < 4:
        return None

    if _has_repeated_word(cleaned):
        return None

    if _is_mostly_non_alpha(cleaned):
        return None

    if _is_noise_bigram(cleaned):
        return None

    if _has_stopword_edges(cleaned):
        return None

    if cleaned in ADMIN_PHRASES:
        return None

    for phrase in ADMIN_PHRASES:
        if cleaned == phrase or cleaned.startswith(f"{phrase} ") or phrase in cleaned:
            return None

    for pattern in SIGNATURE_PATTERNS + HEADER_FOOTER_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return None

    admin_only = {"unit", "marks", "question", "paper", "topics", "contact", "que"}
    words = cleaned.split()
    if words and all(word in admin_only for word in words):
        return None

    return cleaned


def is_valid_topic(topic: str) -> bool:
    return clean_topic(topic) is not None


def filter_topic_frequency(topic_frequency: dict[str, int]) -> dict[str, int]:
    cleaned_counter: dict[str, int] = {}

    for topic, count in topic_frequency.items():
        cleaned = clean_topic(topic)
        if not cleaned:
            continue
        cleaned_counter[cleaned] = cleaned_counter.get(cleaned, 0) + count

    return cleaned_counter
