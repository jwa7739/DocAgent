import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = str(BASE_DIR / "chroma_langchain_db")
COLLECTION_NAME = "docagent"


EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-2")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 6
BATCH_SIZE = 50

# ONE embeddings object, used everywhere (two different model names caused 404s before)
embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})


def count_chunks() -> int:
    return vector_store._collection.count()


def list_sources() -> list:
    """Names of all PDFs currently indexed."""
    data = vector_store.get(include=["metadatas"])
    return sorted({m["source"] for m in (data.get("metadatas") or []) if m and m.get("source")})


def add_document(pdf_path, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> int:
    """Index a PDF. Returns the number of chunks stored."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = PyPDFLoader(str(pdf_path)).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(pages)

    ids = []
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = pdf_path.name
        ids.append(f"{pdf_path.name}::{i}")

    # remove stale chunks if this file was indexed before
    try:
        vector_store._collection.delete(where={"source": pdf_path.name})
    except Exception:
        pass

    for start in range(0, len(chunks), BATCH_SIZE):
        vector_store.add_documents(
            chunks[start:start + BATCH_SIZE],
            ids=ids[start:start + BATCH_SIZE],
        )
    print(f"✓ Indexed {pdf_path.name}: {len(chunks)} chunks")
    return len(chunks)


def get_retriever(pdf_path=None):
    """Backward-compatible helper: optionally index a PDF, then return the retriever."""
    if pdf_path:
        add_document(pdf_path)
    return retriever


print(f"✓ Vector store ready ({count_chunks()} chunks)")