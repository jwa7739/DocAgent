import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from RAG import add_document, list_sources
from src.config import API_DESCRIPTION, API_TITLE, API_VERSION, UPLOADS_DIR
from src.models import ChatRequest, ChatResponse, DocumentResponse, HealthResponse
from src.services.agent_service import agent_service
from src.services.mongo_service import mongo_service
from src.utils.helpers import ensure_directory, safe_filename

app = FastAPI(title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": f"Welcome to {API_TITLE}", "version": API_VERSION, "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="healthy")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    session_id = request.session_id or "default"
    mongo_service.save_message(session_id, "user", question)

    answer, tools, success = agent_service.ask(question)

    mongo_service.save_message(session_id, "assistant", answer, tools)
    return ChatResponse(response=answer, tools=tools, success=success)


@app.post("/upload", response_model=DocumentResponse)
def upload_document(file: UploadFile = File(...)):
    filename = safe_filename(file.filename or "")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    ensure_directory(UPLOADS_DIR)
    path = UPLOADS_DIR / filename
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        chunks = add_document(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not index document: {e}")

    return DocumentResponse(message="Document uploaded and indexed", file=filename, chunks=chunks)


@app.get("/documents")
def documents():
    sources = list_sources()
    return {"documents": sources, "count": len(sources)}


@app.get("/history/{session_id}")
def history(session_id: str):
    return {
        "session_id": session_id,
        "storage_enabled": mongo_service.enabled,
        "messages": mongo_service.get_history(session_id),
    }
