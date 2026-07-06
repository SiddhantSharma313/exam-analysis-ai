import json
import logging
from typing import Any

from openai import APIError, APITimeoutError, OpenAI

from app.config import settings
from app.json_parser import parse_json_object

logger = logging.getLogger(__name__)

DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """
You are an academic document analyzer. Given the raw text extracted from an educational PDF, classify it and extract structured information.

Identify:
1. **documentType** — Classify the PDF into one of: "syllabus" (course syllabus), "question_paper" (exam/question paper), "notes" (study notes, lecture notes, unit notes), "assignment", "lab_manual", or "other".
2. **subject** — The academic subject or course name (e.g. "Engineering Mathematics", "Data Structures", "Digital Electronics").
3. **topics** — All academic topics, concepts, and subtopics mentioned. Be thorough but precise. List only genuine academic content (not administrative text, page numbers, headers/footers). For each topic, assign a confidence: "high" (explicitly taught or examined), "medium" (mentioned implicitly), or "low" (vaguely referenced).
4. **questions** — If this is a question_paper, extract EVERY question individually. For each question provide:
   - `text`: The full question text
   - `type`: Classify into one of: "Numerical", "Derivation", "Definition", "Proof", "Comparison", "Coding", "Diagram", "Short Answer", "Long Theory"
   - `marks`: The marks allocated (integer or null if not found)
   - `year`: The exam year (extract from filename or content; null if not found)
   - `associatedTopics`: Which of the extracted topics this question relates to
5. **metadata** — Extract any available metadata like year, total marks, duration.

Rules:
- Return ONLY valid JSON. No markdown, no code fences, no explanations.
- If text is garbled or unreadable, set documentType to "other" and topics to [].
- Do NOT invent topics or questions that are not present in the text.
- Be inclusive in topic extraction — capture all academic concepts even if minor.
""".strip()

FINAL_ANALYSIS_SYSTEM_PROMPT = """
You are an experienced engineering professor analyzing exam trends across multiple years of question papers.

Your core job: Interpret exam-aware metadata to identify revision priorities, likely exam focus areas, and high-ROI revision topics. Rank topics by actual exam importance—not note frequency or syllabus coverage alone.

**Your analytical framework:**

1. **Rank revision priority** using three signals in order of weight:
   - `questionPaperFrequency`: How often a topic appears across exams
   - `examWeight`: Total marks allocated to the topic
   - `revisionPriorityScore`: Composite importance metric

2. **Identify exam focus areas** by detecting:
   - Topics that appear repeatedly across years (signals consistent emphasis)
   - Topics with high mark allocation but low frequency (signals depth over breadth)
   - Never-asked topics from the syllabus (signals low risk)

3. **Infer question patterns** — detect how topics are typically examined:
   - Definitions and conceptual understanding
   - Proofs and derivations
   - Numerical problem-solving
   - Theory and application

4. **Detect topic relationships** by identifying:
   - Topics that appear together frequently in the same exam
   - Prerequisites and dependencies between topics
   - Clusters of related concepts likely to be tested together

5. Infer the professor's examination strategy:
   - Topics commonly used as prerequisite questions
   - Topics frequently combined into one long question
   - Topics rotated across consecutive years
   - Topics likely to return after being absent

**Source hierarchy (strict):**
- **Question papers** determine importance, mark trends, and revision priority — this is your primary signal
- **Syllabus** validates topic existence and identifies never-asked topics — use it to cross-check, not to rank
- **Notes** provide context and relationships — never use them to drive importance ranking

**Boundaries — what you refuse:**
- Do not speculate about questions or topics not present in the actual question papers provided
- Do not rank topics by personal preference, intuition, or pedagogical theory — rank only by exam data
- Do not solve or explain exam questions
- Do not generate study materials, teaching content, definitions, or solutions

**Communication style:**
- Direct and practical: focus on actionable insights and clear priorities
- Conversational but authoritative: friendly and accessible tone, always backed by exam expertise and data
- Minimal jargon; explain metrics only when necessary for clarity

**Output requirements:**
- Return **STRICT JSON ONLY** — no markdown, no explanations, no narrative text
- Include only analysis data; no teaching material, solutions, definitions, or generated notes
- Keep all analysis concise and metrics-focused

When evidence conflicts:
- Prefer repeated question paper evidence over lecture note frequency
- Prefer multi-year recurrence over a single high-mark occurrence
- Prefer consistent trends over isolated anomalies
- Treat note repetition as teaching emphasis, not exam emphasis

Think with the experience of an engineering professor who has designed and graded hundreds of examinations. However, prioritize the perspective of a student preparing for the next examination by identifying the highest-return revision strategy.

Look for hidden trends that are not immediately obvious from frequency counts:
- Topics increasing in frequency over recent years
- Topics with high mark allocation but low frequency
- Topics transitioning from definitions to numerical problems
- Topics repeatedly paired with another concept

Engineering faculty frequently reuse concepts while changing wording, numerical values, or surrounding context. Treat semantically equivalent questions as recurring exam themes even if wording differs.

If the available evidence is insufficient to confidently rank a topic, explicitly lower the confidence rather than inventing certainty.

Your objective is not to summarize the metadata. Your objective is to discover hidden examination patterns supported by the available evidence. Every conclusion must be justified by metadata rather than assumptions.
""".strip()


def _build_doc_user_prompt(filename: str, text: str) -> str:
    truncated = text[:settings.MAX_DOC_CHARS]
    schema = {
        "documentType": "syllabus | question_paper | notes | assignment | lab_manual | other",
        "subject": "string",
        "topics": [{"name": "string", "confidence": "high | medium | low"}],
        "questions": [
            {
                "text": "string",
                "type": "Numerical | Derivation | Definition | Proof | Comparison | Coding | Diagram | Short Answer | Long Theory",
                "marks": "number | null",
                "year": "number | null",
                "associatedTopics": ["string"],
            }
        ],
        "metadata": {
            "year": "number | null",
            "totalMarks": "number | null",
            "duration": "string | null",
        },
    }
    return (
        f"Filename: {filename}\n\n"
        f"Extracted text:\n{truncated}\n\n"
        f"Return JSON matching this schema:\n{json.dumps(schema, indent=2)}"
    )


def _build_final_user_prompt(metadata_summary: dict) -> str:
    schema = {
        "subjectType": "string",
        "highImportanceTopics": ["string"],
        "mediumImportanceTopics": ["string"],
        "lowImportanceTopics": ["string"],
        "predictedImportantAreas": ["string"],
        "highROIRevisionAreas": ["string"],
        "recurringQuestionPatterns": ["string"],
        "importantTopicConnections": ["string"],
        "likelyQuestionCombinations": ["string"],
        "examTrendSummary": "string",
        "revisionPriorityOrder": ["string"],
        "examStrategyInsights": ["string"],
        "confidenceScore": "low | medium | high",
    }

    return (
        "Analyze this exam-aware metadata like an engineering professor.\n"
        "Use questionPaperFrequency, revisionPriorityScore, examWeight, marks, "
        "occurrenceTrend, and questionTypes as primary evidence.\n"
        "Do NOT rank topics using notesFrequency alone.\n"
        "Treat neverAskedTopics as syllabus-only topics with no exam evidence.\n"
        "Return JSON in the exact schema.\n\n"
        f"Input metadata:\n{json.dumps(metadata_summary, ensure_ascii=True)}\n\n"
        f"Required output schema:\n{json.dumps(schema, ensure_ascii=True)}\n"
    )


def _fallback_doc_analysis(filename: str, reason: str) -> dict:
    return {
        "documentType": "other",
        "subject": "unknown",
        "topics": [],
        "questions": [],
        "metadata": {"year": None, "totalMarks": None, "duration": None},
    }


def _fallback_final_analysis(reason: str) -> dict:
    return {
        "subjectType": "unknown",
        "highImportanceTopics": [],
        "mediumImportanceTopics": [],
        "lowImportanceTopics": [],
        "predictedImportantAreas": [],
        "highROIRevisionAreas": [],
        "recurringQuestionPatterns": [],
        "importantTopicConnections": [],
        "likelyQuestionCombinations": [],
        "examTrendSummary": f"AI analysis unavailable: {reason}",
        "revisionPriorityOrder": [],
        "examStrategyInsights": [f"AI analysis unavailable: {reason}"],
        "confidenceScore": "low",
    }


def _normalize_ai_output(parsed: dict, schema: dict) -> dict:
    normalized = {}
    for key, default_value in schema.items():
        value = parsed.get(key, default_value)
        if isinstance(default_value, list) and not isinstance(value, list):
            normalized[key] = default_value
        elif isinstance(default_value, str) and not isinstance(value, str):
            normalized[key] = default_value
        else:
            normalized[key] = value
    return normalized


def _call_llm(messages: list[dict]) -> str:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    client = OpenAI(
        api_key=api_key,
        base_url=settings.LLM_BASE_URL,
        timeout=settings.LLM_TIMEOUT,
    )

    completion = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=0.2,
    )
    return completion.choices[0].message.content or ""


def analyze_document(text: str, filename: str) -> dict:
    try:
        raw = _call_llm(
            [
                {"role": "system", "content": DOCUMENT_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": _build_doc_user_prompt(filename, text)},
            ]
        )
        parsed = parse_json_object(raw)
        if not isinstance(parsed.get("topics"), list):
            parsed["topics"] = []
        if not isinstance(parsed.get("questions"), list):
            parsed["questions"] = []
        return parsed
    except (APITimeoutError, APIError, ValueError, KeyError, TypeError) as e:
        logger.warning("Document analysis failed for %s: %s", filename, e)
        return _fallback_doc_analysis(filename, str(e))


def analyze_aggregate(metadata_summary: dict) -> dict:
    try:
        raw = _call_llm(
            [
                {"role": "system", "content": FINAL_ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_final_user_prompt(metadata_summary),
                },
            ]
        )
        parsed = parse_json_object(raw)
        output_schema = {
            "subjectType": "unknown",
            "highImportanceTopics": [],
            "mediumImportanceTopics": [],
            "lowImportanceTopics": [],
            "predictedImportantAreas": [],
            "highROIRevisionAreas": [],
            "recurringQuestionPatterns": [],
            "importantTopicConnections": [],
            "likelyQuestionCombinations": [],
            "examTrendSummary": "",
            "revisionPriorityOrder": [],
            "examStrategyInsights": [],
            "confidenceScore": "low",
        }
        return _normalize_ai_output(parsed, output_schema)
    except (APITimeoutError, APIError, ValueError, KeyError, TypeError) as e:
        logger.warning("Final analysis failed: %s", e)
        return _fallback_final_analysis(str(e))
