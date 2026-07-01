# Backend (Current Stage)

This is a minimal FastAPI backend.

## What is included

- Basic FastAPI server setup
- One endpoint: `GET /health`
- One endpoint: `POST /upload` for PDF text extraction
- One endpoint: `POST /analyze-topics` for topic + pattern + lightweight AI analysis

## Run locally

1. Open a terminal in the `backend` folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add environment variable:

- Copy `.env.example` to `.env`
- Set `OPENAI_API_KEY`

4. Start the server:

```bash
uvicorn app.main:app --reload
```

5. Open:
- API root docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

## Upload endpoint

- URL: `POST /upload`
- Body type: `multipart/form-data`
- Field name: `files` (you can send multiple files)
- Accepts: PDF files only
- Returns: filename, extracted raw text, preview, and character count

## Topic analysis endpoint

- URL: `POST /analyze-topics`
- Body type: `multipart/form-data`
- Field name: `files` (you can send multiple files)
- Accepts: PDF files only
- Returns:
  - `detectedTopics`
  - `topicFrequency`
  - `filesAppearedIn`
  - `importanceTier`
  - `neverAskedTopics`
  - `questionPatterns`
  - `aiMetadataSummary`
  - `aiAnalysis`

## Question pattern output inside `questionPatterns`

- `detectedQuestionPatterns`
- `patternFrequency`
- `filesAppearedIn`
- `relatedTopics`
- `highFrequencyPatterns`

## AI output inside `aiAnalysis`

- `subjectType`
- `highImportanceTopics`
- `mediumImportanceTopics`
- `lowImportanceTopics`
- `predictedImportantAreas`
- `highROIRevisionAreas`
- `recurringQuestionPatterns`
- `examStrategyInsights`
- `confidenceScore`
