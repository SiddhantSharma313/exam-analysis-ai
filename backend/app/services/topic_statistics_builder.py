from app.services.importance_scorer import (
    compute_exam_weight,
    compute_occurrence_trend,
    compute_revision_priority_score,
)
from app.services.question_linker import build_topic_question_links


def build_topic_statistics(
    topic: str,
    role_profile: dict,
    link_data: dict,
    max_paper_frequency: int,
    max_papers_appeared: int,
    max_years_appeared: int,
    max_notes_frequency: int,
    total_question_papers: int,
) -> dict:
    """
    Build one evidence-driven topic record for AI metadata.
    Raw frequency is not the primary metric; exam evidence is.
    """
    paper_frequency = role_profile["questionPaperFrequency"]
    note_frequency = role_profile["notesFrequency"]
    papers_appeared = role_profile["papersAppeared"]
    units_appeared = role_profile["unitsAppeared"]
    question_types = link_data.get("questionTypes", [])
    average_marks = link_data.get("averageMarks")
    highest_marks = link_data.get("highestMarks")
    years_appeared = link_data.get("yearsAppeared", [])
    year_counts = link_data.get("yearCounts", {})
    occurrence_trend = compute_occurrence_trend(year_counts)

    revision_priority_score = compute_revision_priority_score(
        question_paper_frequency=paper_frequency,
        max_question_paper_frequency=max_paper_frequency,
        papers_appeared=len(papers_appeared),
        max_papers_appeared=max(max_papers_appeared, 1),
        years_appeared_count=len(years_appeared),
        max_years_appeared=max(max_years_appeared, 1),
        average_marks=average_marks,
        highest_marks=highest_marks,
        question_type_count=len(question_types),
        occurrence_trend=occurrence_trend,
        notes_frequency=note_frequency,
        max_notes_frequency=max(max_notes_frequency, 1),
    )

    return {
        "topic": topic,
        "name": topic,
        "existsInSyllabus": role_profile["existsInSyllabus"],
        "syllabusMentioned": role_profile["existsInSyllabus"],
        "notesFrequency": note_frequency,
        "noteFrequency": note_frequency,
        "questionPaperFrequency": paper_frequency,
        "papersAppeared": len(papers_appeared),
        "unitsAppeared": len(units_appeared),
        "yearsAppeared": years_appeared,
        "firstAppearance": years_appeared[0] if years_appeared else None,
        "lastAppearance": years_appeared[-1] if years_appeared else None,
        "averageMarks": average_marks,
        "highestMarks": highest_marks,
        "questionTypes": question_types,
        "occurrenceTrend": occurrence_trend,
        "neverAsked": paper_frequency == 0 and role_profile["existsInSyllabus"],
        "examWeight": compute_exam_weight(revision_priority_score),
        "revisionPriorityScore": revision_priority_score,
        "occurrenceRatio": round(paper_frequency / max(max_paper_frequency, 1), 2),
        "relativeFrequency": round(paper_frequency / max(total_question_papers, 1), 2),
        # Backward-compatible aliases.
        "frequency": paper_frequency,
        "importanceScore": revision_priority_score,
        "papers": len(papers_appeared),
        "units": len(units_appeared),
        "syllabus": 1 if role_profile["existsInSyllabus"] else 0,
        "lectureNotes": len(role_profile["lectureNotesAppeared"]),
        "files": len(papers_appeared) + len(units_appeared),
    }
