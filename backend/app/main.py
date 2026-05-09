from fastapi import FastAPI


app = FastAPI(title="Exam Analysis AI Backend")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
