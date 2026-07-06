from collections import Counter

from app.services.confidence_engine import (
    AI_CONFIDENCE_THRESHOLD,
    compute_topic_confidence,
    passes_ai_threshold,
)
from app.services.exam_aware_metadata import collect_topic_role_profiles
from app.services.never_asked_detector import compute_never_asked_topics
from app.services.question_linker import build_topic_question_links
from app.services.topic_cleaner import clean_topic
from app.services.topic_statistics_builder import build_topic_statistics

DISPLAY_NAME_OVERRIDES = {
    "Applied Linear Algebra": ["linear algebra", "applied linear"],
    "Engineering Mathematics": ["engineering mathematics", "engineering maths"],
    "Data Structures": ["data structures", "data structure"],
    "Digital Electronics": ["digital electronics", "digital logic"],
}

GENERIC_FILENAMES = {
    "syllabus",
    "question paper",
    "questionpaper",
    "exam paper",
    "previous year",
    "assignment",
    "notes",
    "unit notes",
    "lecture notes",
}


def _infer_subject(documents: list[dict[str, str]]) -> str:
    for document in documents:
        if document["file_type"] == "syllabus":
            filename = document["filename"]
            subject_guess = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
            cleaned = clean_topic(subject_guess.lower())
            if cleaned and len(cleaned) > 4 and cleaned not in GENERIC_FILENAMES:
                return cleaned.title()

    combined_text = " ".join(document["filename"].lower() for document in documents)
    for subject_name, hints in DISPLAY_NAME_OVERRIDES.items():
        if any(hint in combined_text for hint in hints):
            return subject_name

    for document in documents:
        if document["file_type"] == "syllabus" and document["text"].strip():
            heading = document["text"].splitlines()[0].strip()
            cleaned = clean_topic(heading.lower())
            if cleaned and len(cleaned) > 4 and cleaned not in GENERIC_FILENAMES:
                return cleaned.title()

    return "Unknown Subject"


def _build_related_topics(
    topic: str,
    role_profiles: dict[str, dict],
    question_paper_frequency: dict[str, int],
) -> list[str]:
    topic_units = set(role_profiles.get(topic, {}).get("unitsAppeared", []))
    topic_papers = set(role_profiles.get(topic, {}).get("papersAppeared", []))
    overlap_scores: dict[str, int] = {}

    for other_topic, profile in role_profiles.items():
        if other_topic == topic:
            continue
        shared_units = len(topic_units.intersection(profile.get("unitsAppeared", [])))
        shared_papers = len(topic_papers.intersection(profile.get("papersAppeared", [])))
        overlap = shared_units + (shared_papers * 2)
        if overlap > 0:
            overlap_scores[other_topic] = overlap

    ranked = sorted(
        overlap_scores.items(),
        key=lambda item: (item[1], question_paper_frequency.get(item[0], 0)),
        reverse=True,
    )
    return [name for name, _ in ranked[:3]]


def build_intelligent_metadata_summary(
    topic_analysis: dict,
    question_patterns: dict,
    documents: list[dict[str, str]],
    max_topics: int = 12,
) -> dict:
    """
    Stage 7.6 evidence-driven metadata builder.
    Question papers provide importance; notes/syllabus provide context only.
    """
    role_profiles = collect_topic_role_profiles(documents)
    topic_links = build_topic_question_links(documents)
    never_asked = compute_never_asked_topics(documents)
    subject = _infer_subject(documents)

    total_question_papers = sum(
        1 for document in documents if document["file_type"] == "question_paper"
    )

    question_paper_frequency = {
        topic: profile["questionPaperFrequency"]
        for topic, profile in role_profiles.items()
    }
    notes_frequency = {
        topic: profile["notesFrequency"] for topic, profile in role_profiles.items()
    }

    max_paper_frequency = max(question_paper_frequency.values()) if question_paper_frequency else 0
    max_papers_appeared = max(
        (len(profile["papersAppeared"]) for profile in role_profiles.values()),
        default=0,
    )
    max_notes_frequency = max(notes_frequency.values()) if notes_frequency else 0
    max_years_appeared = max(
        (len(topic_links.get(topic, {}).get("yearsAppeared", [])) for topic in topic_links),
        default=0,
    )

    exam_ranked_topics = sorted(
        [
            topic
            for topic, profile in role_profiles.items()
            if profile["questionPaperFrequency"] > 0
        ],
        key=lambda name: question_paper_frequency.get(name, 0),
        reverse=True,
    )

    enriched_topics: list[dict] = []
    for topic in exam_ranked_topics:
        profile = role_profiles[topic]
        link_data = topic_links.get(topic, {})

        stats = build_topic_statistics(
            topic=topic,
            role_profile=profile,
            link_data=link_data,
            max_paper_frequency=max_paper_frequency,
            max_papers_appeared=max_papers_appeared,
            max_years_appeared=max(max_years_appeared, 1),
            max_notes_frequency=max_notes_frequency,
            total_question_papers=total_question_papers,
        )

        confidence_score = compute_topic_confidence(
            {
                "from_heading": False,
                "known_concept": True,
                "from_definition": False,
                "in_syllabus_universe": profile["existsInSyllabus"],
                "in_unit_notes": len(profile["unitsAppeared"]) > 0,
                "in_lecture_notes": len(profile["lectureNotesAppeared"]) > 0,
                "in_question_paper": stats["questionPaperFrequency"] > 0,
                "repeat_count": stats["questionPaperFrequency"],
                "file_count": stats["papersAppeared"] + stats["unitsAppeared"],
                "paper_count": stats["papersAppeared"],
            }
        )

        if not passes_ai_threshold(confidence_score):
            continue

        stats["relatedTopics"] = _build_related_topics(
            topic, role_profiles, question_paper_frequency
        )
        stats["confidenceScore"] = confidence_score
        enriched_topics.append(stats)

    enriched_topics.sort(key=lambda item: item["revisionPriorityScore"], reverse=True)
    enriched_topics = enriched_topics[:max_topics]

    file_type_breakdown = Counter(document["file_type"] for document in documents)

    legacy_top_topics = [
        {"topic": item["name"], "count": item["questionPaperFrequency"]}
        for item in enriched_topics[:10]
    ]
    high_frequency_topics = [
        item["name"] for item in enriched_topics if item["revisionPriorityScore"] >= 70
    ][:10]

    return {
        "subject": subject,
        "filesAnalyzed": len(documents),
        "fileTypeBreakdown": dict(file_type_breakdown),
        "totalQuestionPapers": total_question_papers,
        "scoringModel": "exam_aware_v2",
        "topics": enriched_topics,
        "topTopics": legacy_top_topics,
        "highFrequencyTopics": high_frequency_topics,
        "questionPatterns": question_patterns.get("patternFrequency", {}),
        "highFrequencyPatterns": question_patterns.get("highFrequencyPatterns", []),
        "neverAskedTopics": never_asked[:10],
        "confidenceThreshold": AI_CONFIDENCE_THRESHOLD,
        "topicQuestionLinks": {
            topic: details.get("questionTypes", [])
            for topic, details in list(topic_links.items())[:12]
        },
    }
