from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value):
        if not value.strip():
            raise ValueError("El mensaje de contexto está vacío.")
        return value.strip()


class DeleteDocumentRequest(BaseModel):
    source: str = Field(min_length=1, max_length=500)

    @field_validator("source")
    @classmethod
    def strip_source(cls, value):
        if not value.strip():
            raise ValueError("Selecciona un documento para eliminar.")
        return value.strip()


class DeleteDocumentResponse(BaseModel):
    source: str
    chunks_deleted: int
    total_chunks: int


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=10)
    source: str | None = Field(default=None, max_length=500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value):
        if not value.strip():
            raise ValueError("Escribe una pregunta.")
        return value.strip()

    @field_validator("history")
    @classmethod
    def validate_history(cls, value):
        if len(value) % 2 or any(message.role != ("user" if i % 2 == 0 else "assistant")
                                 for i, message in enumerate(value)):
            raise ValueError("El historial debe contener hasta seis pares usuario/asistente completos.")
        return value


class Citation(BaseModel):
    index: int
    id: str
    source: str
    text: str
    score: float | None
    page: int | None
    chunk_index: int | None
    kind: Literal["chunk", "document_metadata"] = "chunk"


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool
    reason: str | None = None
    resolved_question: str | None = None


class ResolvedQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value):
        if not value.strip():
            raise ValueError("La pregunta reformulada está vacía.")
        return value.strip()


class GeneratedAnswer(BaseModel):
    answer: str = Field(description="Respuesta en español basada solo en la evidencia. Incluye citas como [1] junto a las afirmaciones.")
    abstained: bool = Field(description="True si la evidencia no permite responder la pregunta completa.")
    citation_indices: list[int] = Field(description="Índices de los fragmentos que respaldan la respuesta; no posiciones de página. Vacío al abstenerse.")
