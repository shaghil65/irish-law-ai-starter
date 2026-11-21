import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Irish Law AI API",
    version="0.1.0",
    description=(
        "Stage 1 development API. Legal retrieval and legal answers are deliberately "
        "disabled until an official, version-aware Irish legislation corpus is ingested."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "Irish Law AI API", "stage": 1, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    return {
        "api": "online",
        "stage": 1,
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "legal_corpus_ready": False,
        "answer_engine_ready": False,
        "message": (
            "Development scaffold is running. No legal corpus has been imported, "
            "so this application does not answer legal questions yet."
        ),
    }


@app.post("/api/chat")
def chat(payload: dict):
    question = str(payload.get("question", "")).strip()
    if not question:
        return JSONResponse(status_code=422, content={"detail": "Question is required."})
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The legal answer engine is not enabled yet. Stage 1 only verifies "
                "the application stack; legislation ingestion and retrieval are next."
            ),
            "question_received": question,
        },
    )
