import json


SYSTEM_PROMPT = """
You are an exam-analysis reasoning assistant.

Your job:
- infer likely important exam areas
- identify high ROI revision topics
- identify recurring exam focus trends
- infer theory vs numerical emphasis
- suggest strategic study prioritization

Strict rules:
- Return STRICT JSON ONLY.
- Do not include markdown.
- Do not explain concepts.
- Do not generate notes or study material.
- Do not solve questions.
- Keep output concise and analysis-focused.
""".strip()


def build_user_prompt(metadata_summary: dict) -> str:
    schema = {
        "subjectType": "string",
        "highImportanceTopics": ["string"],
        "mediumImportanceTopics": ["string"],
        "lowImportanceTopics": ["string"],
        "predictedImportantAreas": ["string"],
        "highROIRevisionAreas": ["string"],
        "recurringQuestionPatterns": ["string"],
        "examStrategyInsights": ["string"],
        "confidenceScore": "low | medium | high",
    }

    return (
        "Analyze this compact exam metadata and return JSON in the exact schema.\n\n"
        f"Input metadata:\n{json.dumps(metadata_summary, ensure_ascii=True)}\n\n"
        f"Required output schema:\n{json.dumps(schema, ensure_ascii=True)}\n"
    )
