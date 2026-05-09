# Backend (Stage 2)

This is a minimal FastAPI backend.

## What is included

- Basic FastAPI server setup
- One endpoint: `GET /health`

## Run locally

1. Open a terminal in the `backend` folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the server:

```bash
uvicorn app.main:app --reload
```

4. Open:
- API root docs: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>
