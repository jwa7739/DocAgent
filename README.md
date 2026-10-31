# DocAgent - RAG Chatbot with Tool Routing

Upload PDFs and ask questions about them. A keyword-routed agent retrieves passages from a ChromaDB vector store and answers strictly from the document; questions asking for *latest / recent / current* information are routed to web search instead.

## Features
- PDF ingestion: load, chunk (800 chars, 150 overlap), embed with Gemini, store in ChromaDB
- Re-uploading a file never creates duplicate chunks (deterministic chunk IDs)
- Tool-routed assistant (LangChain tools + Groq) with keyword routing between search_docs and web_search
- Answers are grounded in retrieved text; says so when the document has no answer
- FastAPI backend with Pydantic validation and auto-generated Swagger docs
- Streamlit chat UI with document upload
- Optional MongoDB chat-history storage

## Tech stack
Python · FastAPI · Streamlit · LangChain · Groq (gpt-oss-20b) · Google Gemini Embeddings · ChromaDB · Pydantic · MongoDB (optional)

## Architecture
```
Streamlit UI  ──HTTP──>  FastAPI  ──>  ManualReActAgent ──> search_docs ──> ChromaDB (Gemini embeddings)
                                                         └─> web_search  ──> Serper API
                                        └─> MongoDB (optional chat history)
```

## Project structure
```
DocAgent/
├── main.py              # starts the API
├── run_all.py           # starts API + UI with one command
├── streamlit_app.py     # chat UI
├── Agent.py             # ReAct-style agent + tools
├── RAG.py               # ingestion + retriever
├── src/
│   ├── config.py
│   ├── models.py        # Pydantic schemas
│   ├── endpoints.py     # FastAPI routes
│   ├── services/        # agent_service.py, mongo_service.py
│   └── utils/helpers.py
├── Bonding.pdf          # sample document
└── requirements.txt
```

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env            # then add your API keys
```

## Run
```bash
python run_all.py                 # API + UI together
# or, in two terminals:
python main.py                    # API  -> http://127.0.0.1:8000/docs
streamlit run streamlit_app.py    # UI   -> http://localhost:8501
```

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | health check |
| POST | `/chat` | `{ "question": "...", "session_id": "..." }` -> answer + tools used |
| POST | `/upload` | upload and index a PDF |
| GET | `/documents` | list indexed documents |
| GET | `/history/{session_id}` | chat history (needs MongoDB) |

## Roadmap
- Docker / docker-compose deployment
- Per-document filtering and source citations in the UI
- Retrieval evaluation set
