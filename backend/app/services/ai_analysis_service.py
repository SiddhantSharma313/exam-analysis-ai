import os
from collections import Counter

from openai import APIError, APITimeoutError, OpenAI

from app.prompts.analysis_prompt import SYSTEM_PROMPT, build_user_prompt
from app.utils.json_parser import parse_json_object


def build_ai_metadata_summary(
    topic_analysis: dict, question_patterns: dict, documents: list[dict[str, str]]
) -> dict:
    topic_frequency = topic_analysis.get("topicFrequency", {})
    sorted_topics = sorted(
        topic_frequency.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    top_topics = [
        {"topic": topic, "count": count}
        for topic, count in sorted_topics[:10]
    ]

    file_type_counter = Counter(document["file_type"] for document in documents)

    return {
        "subject": "Unknown Subject",
        "filesAnalyzed": len(documents),
        "fileTypeBreakdown": dict(file_type_counter),
        "topTopics": top_topics,
        "highFrequencyTopics": topic_analysis.get("importanceTier", {}).get(
            "highlyImportant", []
        )[:10],
        "questionPatterns": question_patterns.get("patternFrequency", {}),
        "highFrequencyPatterns": question_patterns.get("highFrequencyPatterns", []),
        "neverAskedTopics": topic_analysis.get("neverAskedTopics", [])[:10],
    }


def _fallback_analysis(reason: str) -> dict:
    return {
        "subjectType": "unknown",
        "highImportanceTopics": [],
        "mediumImportanceTopics": [],
        "lowImportanceTopics": [],
        "predictedImportantAreas": [],
        "highROIRevisionAreas": [],
        "recurringQuestionPatterns": [],
        "examStrategyInsights": [f"AI analysis unavailable: {reason}"],
        "confidenceScore": "low",
    }


def _normalize_ai_output(parsed: dict) -> dict:
    expected_keys = {
        "subjectType": "unknown",
        "highImportanceTopics": [],
        "mediumImportanceTopics": [],
        "lowImportanceTopics": [],
        "predictedImportantAreas": [],
        "highROIRevisionAreas": [],
        "recurringQuestionPatterns": [],
        "examStrategyInsights": [],
        "confidenceScore": "low",
    }

    normalized: dict = {}
    for key, default_value in expected_keys.items():
        value = parsed.get(key, default_value)
        if isinstance(default_value, list) and not isinstance(value, list):
            normalized[key] = default_value
        elif isinstance(default_value, str) and not isinstance(value, str):
            normalized[key] = default_value
        else:
            normalized[key] = value
    return normalized


def run_ai_analysis(metadata_summary: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_analysis("OPENAI_API_KEY is not configured.")

    try:
        client = OpenAI( api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    timeout=20.0,)
        completion = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(metadata_summary)},
            ],
            temperature=0.2,
        )
        raw_output = completion.output_text
        parsed_json = parse_json_object(raw_output)
        return _normalize_ai_output(parsed_json)
    except APITimeoutError:
        return _fallback_analysis("request timed out.")
    except (APIError, ValueError, KeyError, TypeError) as error:
        return _fallback_analysis(str(error))
