import re
from collections import Counter, defaultdict

from app.services.topic_engine import extract_candidate_topics


PATTERN_RULES: dict[str, list[str]] = {
    "Numerical Problems": [
        r"\bcalculate\b",
        r"\bcompute\b",
        r"\bfind\b",
        r"\bnumerical\b",
        r"\bsolve\b",
    ],
    "Derivations": [
        r"\bderive\b",
        r"\bderivation\b",
        r"\bdifferentiate\b",
        r"\bintegrate\b",
    ],
    "Definitions": [
        r"\bdefine\b",
        r"\bwhat is\b",
        r"\bmeaning of\b",
    ],
    "Proofs": [
        r"\bprove\b",
        r"\bshow that\b",
        r"\bjustify\b",
    ],
    "Comparisons": [
        r"\bcompare\b",
        r"\bdifferentiate between\b",
        r"\bcontrast\b",
    ],
    "Coding/Implementation Questions": [
        r"\bimplement\b",
        r"\bwrite (a )?program\b",
        r"\balgorithm\b",
        r"\bpseudocode\b",
        r"\bcode\b",
    ],
    "Circuit Analysis": [
        r"\bcircuit\b",
        r"\bkirchhoff\b",
        r"\bvoltage\b",
        r"\bcurrent\b",
        r"\bresistance\b",
    ],
    "Diagram-Based Questions": [
        r"\bdraw\b",
        r"\bdiagram\b",
        r"\blabeled\b",
        r"\bsketch\b",
    ],
    "Long Theory Questions": [
        r"\bexplain\b",
        r"\bdiscuss\b",
        r"\banalyze\b",
        r"\bdescribe\b",
    ],
    "Short Answer Questions": [
        r"\bshort note\b",
        r"\bbriefly\b",
        r"\bin 2 marks\b",
        r"\bin 3 marks\b",
        r"\bin 5 marks\b",
    ],
}


def _split_into_question_candidates(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates: list[str] = []

    for line in lines:
        if len(line) < 8:
            continue
        if re.match(r"^(q\.?|question|[0-9]+[\)\.]|[a-z][\)\.])", line.lower()):
            candidates.append(line)
            continue
        if "?" in line:
            candidates.append(line)
            continue
        if re.search(r"\b(define|derive|prove|compare|implement|explain|design|calculate|analyze)\b", line.lower()):
            candidates.append(line)

    return candidates


def _detect_patterns_from_question(question_text: str) -> set[str]:
    detected: set[str] = set()
    lowered = question_text.lower()

    for pattern_name, regex_rules in PATTERN_RULES.items():
        if any(re.search(rule, lowered) for rule in regex_rules):
            detected.add(pattern_name)

    marks_match = re.search(r"\((\d+)\s*marks?\)", lowered)
    if marks_match:
        marks = int(marks_match.group(1))
        if marks >= 10:
            detected.add("Long Theory Questions")
        elif marks <= 3:
            detected.add("Short Answer Questions")

    return detected


def analyze_question_patterns(documents: list[dict[str, str]]) -> dict:
    pattern_frequency: Counter[str] = Counter()
    files_appeared_in: dict[str, set[str]] = defaultdict(set)
    related_topics_counter: dict[str, Counter[str]] = defaultdict(Counter)

    for document in documents:
        if document["file_type"] != "question_paper":
            continue

        filename = document["filename"]
        text = document["text"]
        if not text.strip():
            continue

        question_candidates = _split_into_question_candidates(text)

        for question in question_candidates:
            matched_patterns = _detect_patterns_from_question(question)
            if not matched_patterns:
                continue

            question_topics = extract_candidate_topics(question)
            local_topic_counter = Counter(question_topics)

            for pattern in matched_patterns:
                pattern_frequency[pattern] += 1
                files_appeared_in[pattern].add(filename)

                for topic, count in local_topic_counter.items():
                    related_topics_counter[pattern][topic] += count

    detected_patterns = sorted(
        pattern_frequency.keys(),
        key=lambda name: pattern_frequency[name],
        reverse=True,
    )
    high_frequency_patterns = [
        pattern for pattern in detected_patterns if pattern_frequency[pattern] >= 3
    ]

    related_topics = {}
    for pattern in detected_patterns:
        top_topics = [
            topic
            for topic, _count in related_topics_counter[pattern].most_common(5)
            if len(topic) >= 6
        ]
        related_topics[pattern] = top_topics

    return {
        "detectedQuestionPatterns": detected_patterns,
        "patternFrequency": dict(pattern_frequency),
        "filesAppearedIn": {
            pattern: sorted(list(files))
            for pattern, files in files_appeared_in.items()
        },
        "relatedTopics": related_topics,
        "highFrequencyPatterns": high_frequency_patterns,
    }
