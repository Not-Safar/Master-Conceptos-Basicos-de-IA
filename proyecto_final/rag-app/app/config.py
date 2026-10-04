import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseModel):
    api_key: str = Field(default="", repr=False)
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = Field(default=768, ge=128, le=3072)
    generation_model: str = "gemini-3.5-flash-lite"
    generation_thinking_level: Literal["low", "medium", "high"] = "low"
    chunk_size: int = Field(default=300, ge=50, le=600)
    chunk_overlap: int = Field(default=60, ge=0)
    top_k: int = Field(default=4, ge=1, le=10)
    min_score: float = Field(default=0.35, ge=-1, le=1)
    embedding_batch_size: int = Field(default=8, ge=1, le=32)
    chroma_path: Path = ROOT / "chroma"
    data_path: Path = ROOT / "data"
    collection_name: str = "curso_ia"

    @model_validator(mode="after")
    def validate_chunking(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP debe ser menor que CHUNK_SIZE.")
        if self.embedding_model != "gemini-embedding-001":
            raise ValueError("Este cliente implementa gemini-embedding-001; otros modelos requieren adaptar su API y reindexar.")
        return self


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    fields = {}
    for field in Settings.model_fields:
        env = "GOOGLE_API_KEY" if field == "api_key" else field.upper()
        value = os.getenv(env)
        if value is not None and value.strip():
            fields[field] = value.strip()
    if "chroma_path" in fields:
        path = Path(fields["chroma_path"])
        fields["chroma_path"] = path if path.is_absolute() else ROOT / path
    return Settings(**fields)
