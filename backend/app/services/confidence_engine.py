AI_CONFIDENCE_THRESHOLD = 45
EXTRACTION_CONFIDENCE_THRESHOLD = 30

UNIVERSE_FILE_TYPES = {"syllabus", "unit_notes", "lecture_notes"}
EXAM_FILE_TYPES = {"question_paper"}


def compute_topic_confidence(signals: dict) -> int:
    """
    Score one topic from 0-100 using lightweight evidence signals.
    """
    score = 0.0

    if signals.get("from_heading"):
        score += 20
    if signals.get("known_concept"):
        score += 25
    if signals.get("from_definition"):
        score += 15
    if signals.get("in_syllabus_universe"):
        score += 20
    if signals.get("in_unit_notes"):
        score += 10
    if signals.get("in_lecture_notes"):
        score += 8
    if signals.get("in_question_paper"):
        score += 22
    if signals.get("repeat_count", 0) >= 2:
        score += 10
    if signals.get("repeat_count", 0) >= 4:
        score += 8
    if signals.get("file_count", 0) >= 2:
        score += 10
    if signals.get("paper_count", 0) >= 2:
        score += 12

    return int(min(round(score), 100))


def passes_extraction_threshold(confidence: int) -> bool:
    return confidence >= EXTRACTION_CONFIDENCE_THRESHOLD


def passes_ai_threshold(confidence: int) -> bool:
    return confidence >= AI_CONFIDENCE_THRESHOLD
