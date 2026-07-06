from collections import Counter, defaultdict

from app.services.never_asked_detector import compute_never_asked_topics
from app.services.semantic_topic_extractor import extract_semantic_topics
from app.services.topic_validator import is_valid_academic_topic

UNIVERSE_FILE_TYPES = {"syllabus", "unit_notes", "lecture_notes"}
EXAM_FILE_TYPES = {"question_paper"}


def classify_file_type(filename: str) -> str:
    name = filename.lower()
    if "syllabus" in name:
        return "syllabus"
    if "assignment" in name:
        return "assignment"
    if "lab" in name or "manual" in name:
        return "lab_manual"
    if "unit" in name:
        return "unit_notes"
    if "lecture" in name or "notes" in name:
        return "lecture_notes"
    if "question" in name or "paper" in name or "exam" in name:
        return "question_paper"
    return "other"


def extract_candidate_topics(text: str, file_type: str = "other") -> list[str]:
    from app.services.semantic_topic_extractor import extract_semantic_topic_names

    return extract_semantic_topic_names(text, file_type)


def analyze_topics_from_documents(documents: list[dict[str, str]]) -> dict:
    universe_topics: set[str] = set()
    universe_frequency: Counter[str] = Counter()
    exam_frequency: Counter[str] = Counter()
    exam_files: dict[str, set[str]] = defaultdict(set)
    all_files: dict[str, set[str]] = defaultdict(set)

    for document in documents:
        filename = document["filename"]
        text = document["text"]
        file_type = document["file_type"]

        if not text.strip():
            continue

        extracted = extract_semantic_topics(text, file_type)
        for item in extracted:
            topic = item["name"]
            if not is_valid_academic_topic(topic):
                continue

            count = item["count"]
            all_files[topic].add(filename)

            if file_type in UNIVERSE_FILE_TYPES:
                universe_topics.add(topic)
                universe_frequency[topic] += count

            if file_type in EXAM_FILE_TYPES:
                exam_frequency[topic] += count
                exam_files[topic].add(filename)

    importance_tier = {
        "highlyImportant": [],
        "mediumImportance": [],
        "lowImportance": [],
        "neverAsked": [],
    }

    exam_topic_names = set(exam_frequency.keys())
    never_asked_topics = compute_never_asked_topics(documents)
    importance_tier["neverAsked"] = never_asked_topics

    exam_only_topics = exam_topic_names - set(never_asked_topics)
    for topic in sorted(
        exam_only_topics,
        key=lambda name: (exam_frequency.get(name, 0), universe_frequency.get(name, 0)),
        reverse=True,
    ):
        exam_count = exam_frequency.get(topic, 0)
        paper_count = len(exam_files.get(topic, set()))

        if exam_count >= 8 or paper_count >= 3:
            importance_tier["highlyImportant"].append(topic)
        elif exam_count >= 4 or paper_count >= 2:
            importance_tier["mediumImportance"].append(topic)
        elif exam_count > 0:
            importance_tier["lowImportance"].append(topic)

    all_topics = set(never_asked_topics) | exam_topic_names
    detected_topics = sorted(
        all_topics,
        key=lambda name: (exam_frequency.get(name, 0), universe_frequency.get(name, 0)),
        reverse=True,
    )

    topic_frequency: dict[str, int] = {}
    for topic in detected_topics:
        if topic in exam_frequency:
            topic_frequency[topic] = exam_frequency[topic]
        else:
            topic_frequency[topic] = universe_frequency.get(topic, 0)

    return {
        "detectedTopics": detected_topics,
        "topicFrequency": topic_frequency,
        "filesAppearedIn": {
            topic: sorted(list(files)) for topic, files in all_files.items()
        },
        "importanceTier": importance_tier,
        "neverAskedTopics": never_asked_topics,
    }
