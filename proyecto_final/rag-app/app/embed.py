import math
import time
from collections.abc import Callable

from google import genai
from google.genai import errors, types

from app.config import Settings
from app.errors import RagError


class GoogleProvider:
    """Único proveedor de producción: Google AI Studio, nunca embeddings locales."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @property
    def client(self):
        if not self.settings.api_key:
            raise RagError("Falta GOOGLE_API_KEY. Configura rag-app/.env y reinicia la API.", 503)
        if self._client is None:
            self._client = genai.Client(
                api_key=self.settings.api_key,
                http_options=types.HttpOptions(timeout=60_000),
            )
        return self._client

    def call(self, operation: Callable):
        for attempt in range(3):
            try:
                return operation()
            except RagError:
                raise
            except errors.APIError as exc:
                code = int(exc.code or 500)
                if code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                if code in {401, 403}:
                    raise RagError("Google AI rechazó la clave o los permisos. Revisa tu configuración.", 503) from None
                if code == 429:
                    raise RagError("Google AI alcanzó la cuota. Espera o revisa los límites en AI Studio.", 429) from None
                raise RagError("Google AI no pudo completar la petición. Revisa el modelo, la cuota y la configuración.", 502) from None
            except Exception:
                raise RagError("No se pudo conectar con Google AI. Revisa la conexión y vuelve a intentar.", 502) from None

    def embed(self, texts: list[str], query: bool = False) -> list[list[float]]:
        vectors = []
        for start in range(0, len(texts), self.settings.embedding_batch_size):
            batch = texts[start:start + self.settings.embedding_batch_size]
            response = self.call(lambda: self.client.models.embed_content(
                model=self.settings.embedding_model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY" if query else "RETRIEVAL_DOCUMENT",
                    output_dimensionality=self.settings.embedding_dimensions,
                ),
            ))
            if not response.embeddings or len(response.embeddings) != len(batch):
                raise RagError("Google AI devolvió un lote de embeddings incompleto.", 502)
            for item in response.embeddings:
                values = item.values or []
                norm = math.sqrt(sum(value * value for value in values))
                if len(values) != self.settings.embedding_dimensions or not math.isfinite(norm) or norm == 0:
                    raise RagError("Google AI devolvió un embedding inválido.", 502)
                vectors.append([value / norm for value in values])
        return vectors

    def close(self):
        if self._client:
            self._client.close()
