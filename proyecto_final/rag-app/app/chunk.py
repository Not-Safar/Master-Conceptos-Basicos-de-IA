from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    index: int
    start_word: int
    end_word: int


def chunk_text(text: str, size: int = 300, overlap: int = 60) -> list[Chunk]:
    """Ventanas de palabras; los offsets usan intervalos [inicio, fin)."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Se requiere size > overlap >= 0.")
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(Chunk(" ".join(words[start:end]), len(chunks), start, end))
        if end == len(words):
            break
        start = end - overlap
    return chunks
