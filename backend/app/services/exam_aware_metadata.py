from collections import Counter, defaultdict

from app.services.semantic_topic_extractor import extract_semantic_topics
from app.services.topic_validator import is_valid_academic_topic

SYLLABUS_FILE_TYPE = "syllabus"
NOTES_FILE_TYPES = {"unit_notes", "lecture_notes"}
EXAM_FILE_TYPE = "question_paper"


def collect_topic_role_profiles(
    documents: list[dict[str, str]],
) -> dict[str, dict]:
    """
    Build per-topic document-role statistics.
    Syllabus and notes provide context; question papers provide exam evidence.
    """
    profiles: dict[str, dict] = defaultdict(
        lambda: {
            "existsInSyllabus": False,
            "syllabusFrequency": 0,
            "notesFrequency": 0,
            "questionPaperFrequency": 0,
            "papersAppeared": set(),
            "unitsAppeared": set(),
            "lectureNotesAppeared": set(),
        }
    )

    for document in documents:
        file_type = document["file_type"]
        filename = document["filename"]
        text = document["text"]
        if not text.strip():
            continue

        extracted = extract_semantic_topics(text, file_type)
        for item in extracted:
            topic = item["name"]
            if not is_valid_academic_topic(topic):
                continue
            count = item["count"]
            profile = profiles[topic]

            if file_type == SYLLABUS_FILE_TYPE:
                profile["existsInSyllabus"] = True
                profile["syllabusFrequency"] += count

            if file_type in NOTES_FILE_TYPES:
                profile["notesFrequency"] += count
                if file_type == "unit_notes":
                    profile["unitsAppeared"].add(filename)
                if file_type == "lecture_notes":
                    profile["lectureNotesAppeared"].add(filename)

            if file_type == EXAM_FILE_TYPE:
                profile["questionPaperFrequency"] += count
                profile["papersAppeared"].add(filename)

    serializable: dict[str, dict] = {}
    for topic, profile in profiles.items():
        serializable[topic] = {
            "existsInSyllabus": profile["existsInSyllabus"],
            "syllabusFrequency": profile["syllabusFrequency"],
            "notesFrequency": profile["notesFrequency"],
            "questionPaperFrequency": profile["questionPaperFrequency"],
            "papersAppeared": sorted(profile["papersAppeared"]),
            "unitsAppeared": sorted(profile["unitsAppeared"]),
            "lectureNotesAppeared": sorted(profile["lectureNotesAppeared"]),
        }

    return serializable
