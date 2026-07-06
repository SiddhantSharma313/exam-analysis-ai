from app.services.semantic_topic_extractor import extract_semantic_topics
from app.services.topic_normalizer import canonicalize_topic
from app.services.topic_validator import is_valid_academic_topic

SYLLABUS_FILE_TYPE = "syllabus"
EXAM_FILE_TYPE = "question_paper"


def _collect_canonical_topics(documents: list[dict[str, str]], file_types: set[str]) -> set[str]:
    topics: set[str] = set()

    for document in documents:
        if document["file_type"] not in file_types:
            continue

        extracted = extract_semantic_topics(document["text"], document["file_type"])
        for item in extracted:
            topic = item["name"]
            if is_valid_academic_topic(topic):
                topics.add(canonicalize_topic(topic))

    return topics


def compute_never_asked_topics(documents: list[dict[str, str]]) -> list[str]:
    """
    Compare canonical syllabus topics (Set A) against canonical exam topics (Set B).
    Only genuine academic concepts can appear in the never-asked list.
    """
    syllabus_topics = _collect_canonical_topics(documents, {SYLLABUS_FILE_TYPE})
    exam_topics = _collect_canonical_topics(documents, {EXAM_FILE_TYPE})

    never_asked = sorted(topic for topic in syllabus_topics if topic not in exam_topics)
    return never_asked
