def compute_occurrence_trend(year_counts: dict[str, int]) -> str:
    if len(year_counts) < 2:
        return "stable"

    sorted_years = sorted(year_counts.keys())
    midpoint = len(sorted_years) // 2
    older_years = sorted_years[:midpoint]
    newer_years = sorted_years[midpoint:]

    older_total = sum(year_counts.get(year, 0) for year in older_years)
    newer_total = sum(year_counts.get(year, 0) for year in newer_years)

    if newer_total > older_total * 1.2:
        return "increasing"
    if older_total > newer_total * 1.2:
        return "decreasing"
    return "stable"


def compute_exam_weight(revision_priority_score: int) -> str:
    if revision_priority_score >= 85:
        return "Very High"
    if revision_priority_score >= 70:
        return "High"
    if revision_priority_score >= 45:
        return "Medium"
    if revision_priority_score >= 20:
        return "Low"
    return "Very Low"


def compute_revision_priority_score(
    question_paper_frequency: int,
    max_question_paper_frequency: int,
    papers_appeared: int,
    max_papers_appeared: int,
    years_appeared_count: int,
    max_years_appeared: int,
    average_marks: float | None,
    highest_marks: int | None,
    question_type_count: int,
    occurrence_trend: str,
    notes_frequency: int,
    max_notes_frequency: int,
) -> int:
    """
    Revision priority (0-100). Question papers dominate; notes add confidence only.

    Weighting:
    - Question paper frequency: 35%
    - Papers appeared: 10%
    - Years appeared: 10%
    - Marks (avg + highest): 15%
    - Question type diversity: 15%
    - Occurrence trend: 10%
    - Notes coverage: 5% (minor influence only)
    """
    paper_frequency_score = 0.0
    if max_question_paper_frequency > 0:
        paper_frequency_score = (
            question_paper_frequency / max_question_paper_frequency
        ) * 35

    papers_appeared_score = 0.0
    if max_papers_appeared > 0:
        papers_appeared_score = (papers_appeared / max_papers_appeared) * 10

    years_score = 0.0
    if max_years_appeared > 0:
        years_score = (years_appeared_count / max_years_appeared) * 10

    marks_score = 0.0
    if average_marks is not None:
        marks_score += min(average_marks / 10, 1.0) * 10
    if highest_marks is not None:
        marks_score += min(highest_marks / 15, 1.0) * 5

    type_diversity_score = min(question_type_count, 4) / 4 * 15

    trend_score = {
        "increasing": 10,
        "stable": 6,
        "decreasing": 3,
    }.get(occurrence_trend, 5)

    notes_score = 0.0
    if max_notes_frequency > 0:
        notes_score = (notes_frequency / max_notes_frequency) * 5

    total = (
        paper_frequency_score
        + papers_appeared_score
        + years_score
        + marks_score
        + type_diversity_score
        + trend_score
        + notes_score
    )
    return int(min(round(total), 100))


def compute_importance_score(
    frequency: int,
    max_frequency: int,
    file_count: int,
    question_paper_count: int,
    unit_count: int,
    question_type_count: int,
    average_marks: float | None,
    occurrence_ratio: float,
) -> int:
    """Backward-compatible wrapper."""
    return compute_revision_priority_score(
        question_paper_frequency=frequency,
        max_question_paper_frequency=max_frequency,
        papers_appeared=question_paper_count,
        max_papers_appeared=max(file_count, question_paper_count, 1),
        years_appeared_count=question_paper_count,
        max_years_appeared=max(question_paper_count, 1),
        average_marks=average_marks,
        highest_marks=int(average_marks) if average_marks else None,
        question_type_count=question_type_count,
        occurrence_trend="stable",
        notes_frequency=unit_count,
        max_notes_frequency=max(unit_count, 1),
    )
