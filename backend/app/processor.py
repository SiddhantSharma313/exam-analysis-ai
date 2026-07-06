from collections import defaultdict

from app.config import settings
from app.llm import analyze_document


class TopicInfo:
    def __init__(self, name: str, confidence: str = "low"):
        self.name = name
        self.confidence = confidence


class QuestionInfo:
    def __init__(self, text: str, qtype: str, marks: int | None, year: int | None, topics: list[str]):
        self.text = text
        self.type = qtype
        self.marks = marks
        self.year = year
        self.associated_topics = topics


class DocResult:
    def __init__(self, filename: str, document_type: str, subject: str, topics: list[TopicInfo], questions: list[QuestionInfo], metadata: dict):
        self.filename = filename
        self.document_type = document_type
        self.subject = subject
        self.topics = topics
        self.questions = questions
        self.metadata = metadata


def _parse_doc_response(raw: dict, filename: str) -> DocResult:
    doc_type = raw.get("documentType", "other")
    subject = raw.get("subject", "unknown")
    raw_topics = raw.get("topics", [])
    raw_questions = raw.get("questions", [])
    metadata = raw.get("metadata", {})

    topics = []
    for t in raw_topics:
        if isinstance(t, dict) and t.get("name"):
            topics.append(TopicInfo(name=t["name"], confidence=t.get("confidence", "low")))

    questions = []
    for q in raw_questions:
        if isinstance(q, dict) and q.get("text"):
            questions.append(
                QuestionInfo(
                    text=q["text"],
                    qtype=q.get("type", "Short Answer"),
                    marks=q.get("marks"),
                    year=q.get("year"),
                    topics=q.get("associatedTopics", []),
                )
            )

    return DocResult(
        filename=filename,
        document_type=doc_type,
        subject=subject,
        topics=topics,
        questions=questions,
        metadata=metadata,
    )


def process_documents(files: list[dict]) -> list[DocResult]:
    results = []
    for file in files:
        filename = file["filename"]
        text = file["text"]
        raw = analyze_document(text, filename)
        doc = _parse_doc_response(raw, filename)
        results.append(doc)
    return results


def aggregate_results(doc_results: list[DocResult]) -> dict:
    topic_freq: dict[str, int] = defaultdict(int)
    topic_files: dict[str, list[str]] = defaultdict(list)
    topic_question_types: dict[str, set[str]] = defaultdict(set)
    topic_total_marks: dict[str, list[int]] = defaultdict(list)
    topic_years: dict[str, set[int]] = defaultdict(set)

    syllabus_topics: set[str] = set()
    exam_topics: set[str] = set()
    notes_topics: set[str] = set()

    pattern_freq: dict[str, int] = defaultdict(int)
    pattern_files: dict[str, set[str]] = defaultdict(set)
    pattern_topics: dict[str, set[str]] = defaultdict(set)

    all_questions: list[QuestionInfo] = []

    for doc in doc_results:
        for topic in doc.topics:
            name = topic.name
            topic_freq[name] += 1
            topic_files[name].append(doc.filename)

            if doc.document_type == "syllabus":
                syllabus_topics.add(name)
            elif doc.document_type == "question_paper":
                exam_topics.add(name)
            elif doc.document_type in ("notes", "unit_notes", "lecture_notes"):
                notes_topics.add(name)

        for q in doc.questions:
            all_questions.append(q)
            pattern_freq[q.type] += 1
            pattern_files[q.type].add(doc.filename)
            for t in q.associated_topics:
                pattern_topics[q.type].add(t)
                topic_question_types[t].add(q.type)
                if q.marks:
                    topic_total_marks[t].append(q.marks)
                if q.year:
                    topic_years[t].add(q.year)

    exam_freq: dict[str, int] = defaultdict(int)
    for doc in doc_results:
        if doc.document_type == "question_paper":
            for topic in doc.topics:
                exam_freq[topic.name] += 1

    high: list[str] = sorted(t for t, f in exam_freq.items() if f >= 3)
    med: list[str] = sorted(t for t, f in exam_freq.items() if 2 <= f < 3 and t not in high)
    low: list[str] = sorted(t for t, f in exam_freq.items() if 1 <= f < 2 and t not in high and t not in med)
    never: list[str] = sorted(syllabus_topics - exam_topics)

    high_freq_patterns = [p for p, f in pattern_freq.items() if f >= 3]

    return {
        "detectedTopics": sorted(topic_freq.keys()),
        "topicFrequency": dict(topic_freq),
        "filesAppearedIn": {t: list(set(files)) for t, files in topic_files.items()},
        "importanceTier": {
            "highlyImportant": high,
            "mediumImportance": med,
            "lowImportance": low,
            "neverAsked": never,
        },
        "neverAskedTopics": never,
        "questionPatterns": {
            "detectedQuestionPatterns": sorted(pattern_freq.keys()),
            "patternFrequency": dict(pattern_freq),
            "filesAppearedIn": {p: sorted(fs) for p, fs in pattern_files.items()},
            "relatedTopics": {p: sorted(ts) for p, ts in pattern_topics.items()},
            "highFrequencyPatterns": high_freq_patterns,
        },
        "questionPatternsArray": [
            {"type": p, "frequency": f, "files": sorted(pattern_files.get(p, set()))}
            for p, f in sorted(pattern_freq.items(), key=lambda x: -x[1])
        ],
        "topicStatistics": [
            {
                "name": t,
                "frequency": topic_freq[t],
                "questionPaperFrequency": exam_freq.get(t, 0),
                "questionTypes": sorted(topic_question_types.get(t, set())),
                "averageMarks": (
                    round(sum(topic_total_marks[t]) / len(topic_total_marks[t]), 1)
                    if topic_total_marks.get(t)
                    else None
                ),
                "yearsAppeared": sorted(topic_years.get(t, set())),
                "filesAppearedIn": len(set(topic_files.get(t, []))),
            }
            for t in sorted(topic_freq.keys())
        ],
    }


def build_metadata_summary(aggregated: dict) -> dict:
    topic_stats = aggregated.get("topicStatistics", [])
    topic_stats.sort(key=lambda x: -x["questionPaperFrequency"])
    topic_stats = topic_stats[: settings.TOPIC_LIMIT]

    return {
        "subjectType": "inferred from documents",
        "topicCount": len(aggregated.get("detectedTopics", [])),
        "totalPapers": len(
            set(
                f
                for files in aggregated.get("filesAppearedIn", {}).values()
                for f in files
            )
        ),
        "topicStatistics": topic_stats,
        "questionPatterns": aggregated.get("questionPatternsArray", []),
        "neverAskedTopics": aggregated.get("neverAskedTopics", []),
    }
