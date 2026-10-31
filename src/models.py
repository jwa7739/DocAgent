from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    tools: List[str]
    success: bool


class DocumentResponse(BaseModel):
    message: str
    file: str
    chunks: int = 0


class HealthResponse(BaseModel):
    status: str
