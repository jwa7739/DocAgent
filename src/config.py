import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"

API_TITLE = "DocAgent API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "RAG chatbot with a ReAct-style agent over uploaded PDF documents"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = False  # reload re-imports ChromaDB in a child process and breaks startup
