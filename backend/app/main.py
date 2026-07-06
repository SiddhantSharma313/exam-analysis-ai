from pydantic import BaseModel
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from dotenv import load_dotenv

from app.services.ai_analysis_service import build_ai_metadata_summary, run_ai_analysis
from app.services.question_pattern_engine import analyze_question_patterns
from app.services.topic_engine import analyze_topics_from_documents, classify_file_type

load_dotenv()


app = FastAPI(title="Exam Analysis AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractedFileResult(BaseModel):
    filename: str
    text: str
    preview: str
    characters: int


class UploadResponse(BaseModel):
    total_files: int
    files: list[ExtractedFileResult]


class ImportanceTier(BaseModel):
    highlyImportant: list[str]
    mediumImportance: list[str]
    lowImportance: list[str]
    neverAsked: list[str]


class TopicAnalysisResponse(BaseModel):
    detectedTopics: list[str]
    topicFrequency: dict[str, int]
    filesAppearedIn: dict[str, list[str]]
    importanceTier: ImportanceTier
    neverAskedTopics: list[str]


class QuestionPatternResponse(BaseModel):
    detectedQuestionPatterns: list[str]
    patternFrequency: dict[str, int]
    filesAppearedIn: dict[str, list[str]]
    relatedTopics: dict[str, list[str]]
    highFrequencyPatterns: list[str]


class AIAnalysisResponse(BaseModel):
    subjectType: str
    highImportanceTopics: list[str]
    mediumImportanceTopics: list[str]
    lowImportanceTopics: list[str]
    predictedImportantAreas: list[str]
    highROIRevisionAreas: list[str]
    recurringQuestionPatterns: list[str]
    importantTopicConnections: list[str] = []
    likelyQuestionCombinations: list[str] = []
    examTrendSummary: str = ""
    revisionPriorityOrder: list[str] = []
    examStrategyInsights: list[str]
    confidenceScore: str


class FullAnalysisResponse(TopicAnalysisResponse):
    questionPatterns: QuestionPatternResponse
    aiMetadataSummary: dict
    aiAnalysis: AIAnalysisResponse


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload_pdfs(files: list[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one PDF.")

    results: list[ExtractedFileResult] = []

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a PDF file.",
            )

        try:
            pdf_reader = PdfReader(file.file)
            extracted_text_parts: list[str] = []

            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                extracted_text_parts.append(page_text)

            full_text = "\n".join(extracted_text_parts).strip()
            preview = full_text[:500] if full_text else "No text found in this PDF."

            results.append(
                ExtractedFileResult(
                    filename=file.filename or "unknown.pdf",
                    text=full_text,
                    preview=preview,
                    characters=len(full_text),
                )
            )
        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read {file.filename} as a PDF.",
            ) from error
        finally:
            await file.close()

    return UploadResponse(total_files=len(results), files=results)


@app.post("/analyze-topics", response_model=FullAnalysisResponse)
async def analyze_topics(files: list[UploadFile] = File(...)) -> FullAnalysisResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one PDF.")

    documents: list[dict[str, str]] = []

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a PDF file.",
            )

        try:
            pdf_reader = PdfReader(file.file)
            extracted_text_parts: list[str] = []

            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                extracted_text_parts.append(page_text)

            full_text = "\n".join(extracted_text_parts).strip()
            documents.append(
                {
                    "filename": file.filename or "unknown.pdf",
                    "file_type": classify_file_type(file.filename or ""),
                    "text": full_text,
                }
            )
        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read {file.filename} as a PDF.",
            ) from error
        finally:
            await file.close()

    topic_analysis_result = analyze_topics_from_documents(documents)
    question_pattern_result = analyze_question_patterns(documents)
    ai_metadata_summary = build_ai_metadata_summary(
        topic_analysis=topic_analysis_result,
        question_patterns=question_pattern_result,
        documents=documents,
    )
    ai_analysis = run_ai_analysis(ai_metadata_summary)

    return FullAnalysisResponse(
        **topic_analysis_result,
        questionPatterns=QuestionPatternResponse(**question_pattern_result),
        aiMetadataSummary=ai_metadata_summary,
        aiAnalysis=AIAnalysisResponse(**ai_analysis),
    )
