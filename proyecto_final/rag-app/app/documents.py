from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.errors import RagError

MAX_BYTES = 10 * 1024 * 1024
SUPPORTED = {".txt", ".md", ".pdf"}


@dataclass(frozen=True)
class Page:
    text: str
    number: int


@dataclass(frozen=True)
class Document:
    source: str
    pages: list[Page]


def parse_document(source: str, content: bytes) -> Document:
    suffix = Path(source).suffix.lower()
    if suffix not in SUPPORTED:
        raise RagError(f"{source}: solo se admiten PDF, Markdown y TXT.")
    if len(content) > MAX_BYTES:
        raise RagError(f"{source}: excede el límite de 10 MiB.", 413)
    try:
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise RagError(f"{source}: PDF protegido; proporciona una copia sin contraseña.")
            pages = [Page(page.extract_text() or "", n) for n, page in enumerate(reader.pages, 1)]
        else:
            pages = [Page(content.decode("utf-8-sig"), 1)]
    except RagError:
        raise
    except Exception:
        raise RagError(f"{source}: no se pudo leer. TXT/MD deben estar en UTF-8 y PDF debe contener texto.") from None
    if not any(page.text.strip() for page in pages):
        raise RagError(f"{source}: sin texto extraíble. Los PDF escaneados requieren OCR.")
    return Document(source, pages)


def resolve_paths(raw_paths: list[str], data_path: Path) -> list[Path]:
    """El selector de carpeta solo puede leer dentro de data/."""
    root = data_path.resolve()
    found = []
    for raw in raw_paths:
        candidate = Path(raw)
        candidate = (candidate if candidate.is_absolute() else root / candidate).resolve()
        if not candidate.is_relative_to(root):
            raise RagError("Las rutas deben estar dentro de data/.")
        if not candidate.exists():
            raise RagError(f"Ruta inexistente en data/: {raw}")
        paths = sorted(candidate.rglob("*")) if candidate.is_dir() else [candidate]
        for path in paths:
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise RagError("La carpeta contiene enlaces fuera de data/.")
            if path.is_file() and path.suffix.lower() in SUPPORTED:
                found.append(resolved)
    return list(dict.fromkeys(found))
