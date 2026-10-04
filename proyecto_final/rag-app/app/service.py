import hashlib
from pathlib import Path
from threading import RLock

from app.chunk import chunk_text
from app.config import Settings
from app.conversation import resolve_question
from app.documents import Document
from app.embed import GoogleProvider
from app.errors import RagError
from app.generate import abstain, generate_answer
from app.retrieval import contents_text, page_count_question, positional_question
from app.schemas import Citation, DeleteDocumentResponse, QueryRequest
from app.store import ChromaStore


class RagService:
    def __init__(self, settings: Settings, store: ChromaStore, provider: GoogleProvider):
        self.settings, self.store, self.provider = settings, store, provider
        self.lock = RLock()

    def delete_document(self, source: str) -> DeleteDocumentResponse:
        with self.lock:
            deleted = self.store.delete_source(source)
            if not deleted:
                raise RagError("Este archivo ya no está en el índice. Actualiza el estado de la biblioteca.", 404)
            return DeleteDocumentResponse(source=source, chunks_deleted=deleted, total_chunks=self.store.count())

    def ingest(self, documents: list[Document]):
        with self.lock:
            if not documents:
                raise RagError("Selecciona al menos un documento válido.")
            if len({d.source for d in documents}) != len(documents):
                raise RagError("Hay nombres de documento duplicados en la petición.")
            prepared, skipped, metadata_updates = [], [], []
            for doc in documents:
                fingerprint = hashlib.sha256("\n".join(p.text for p in doc.pages).encode()).hexdigest()
                texts, metadata, ids = [], [], []
                for page in doc.pages:
                    for chunk in chunk_text(page.text, self.settings.chunk_size, self.settings.chunk_overlap):
                        text = chunk.text
                        texts.append(text)
                        ids.append(hashlib.sha256(f"{doc.source}:{fingerprint}:{page.number}:{chunk.index}".encode()).hexdigest())
                        metadata.append({"source": doc.source, "page": page.number, "chunk_index": chunk.index,
                                         "start_word": chunk.start_word, "end_word": chunk.end_word,
                                         "fingerprint": fingerprint, "file_type": Path(doc.source).suffix.lower(),
                                         "is_contents": contents_text(page.text)})
                        if Path(doc.source).suffix.lower() == ".pdf":
                            metadata[-1]["pdf_page_count"] = len(doc.pages)
                if self.store.unchanged(doc.source, fingerprint):
                    skipped.append(doc.source)
                    metadata_updates.append((ids, metadata))
                    continue
                vectors = self.provider.embed(texts)
                prepared.append((doc.source, ids, texts, vectors, metadata))
            # Ninguna escritura al índice hasta completar todas las llamadas a Google.
            for record in prepared:
                self.store.replace(*record)
            for ids, metadata in metadata_updates:
                self.store.refresh_metadata(ids, metadata)
            return {"documents_indexed": len(prepared), "chunks_indexed": sum(len(r[1]) for r in prepared),
                    "documents_skipped": skipped, "total_chunks": self.store.count()}

    def query(self, request: QueryRequest):
        with self.lock:
            if not self.store.count():
                return abstain("El índice está vacío. Carga e indexa documentos primero.")
            documents = self.store.documents()
            if request.source and request.source not in {d["source"] for d in documents}:
                return abstain("No hay documentos para el filtro solicitado.")
            question = resolve_question(self.provider, request.question, request.history, request.source)
            result = self._query_resolved(request, question, documents)
            return result.model_copy(update={"resolved_question": question if request.history else None})

    def _query_resolved(self, request: QueryRequest, question: str, documents: list[dict]):
        top_k = request.top_k or self.settings.top_k
        position = positional_question(question)
        metadata_citation = None
        if page_count_question(question):
            pdfs = [d["source"] for d in documents if d["source"].lower().endswith(".pdf")
                    and (not request.source or d["source"] == request.source)]
            if len(pdfs) > 1:
                return abstain("Hay varios PDF. Selecciona el archivo en 'Buscar en' para consultar sus páginas.")
            if not pdfs:
                return abstain("No hay un PDF indexado para consultar su número de páginas.")
            page_count = self.store.pdf_page_count(pdfs[0])
            if page_count is None:
                return abstain("Este PDF se indexó sin guardar el total de páginas. Vuelve a indexarlo una vez para actualizar sus metadatos; no se repetirán embeddings si no cambió.")
            metadata_citation = Citation(index=1, id="metadata:" + hashlib.sha256(pdfs[0].encode()).hexdigest(),
                source=pdfs[0], page=None, chunk_index=None, score=None, kind="document_metadata",
                text=f"Metadatos del archivo {pdfs[0]}. Número total de páginas físicas del PDF: {page_count}. "
                     "Recuento obtenido por pypdf al leer el archivo original; incluye páginas sin texto. "
                     "Es el total de este archivo PDF, no el número de la última página impresa ni el total de una edición completa si es un extracto.")
        vector = self.provider.embed([question], query=True)[0]
        retrieved = self.store.search(vector, max(12, top_k * 3) if position else top_k, request.source)
        evidence = [c for c in retrieved if c.score is not None and c.score >= self.settings.min_score]
        if position:
            contents = self.store.contents(vector, 20, request.source)
            contents = [c for c in contents if c.score is not None and c.score >= self.settings.min_score]
            contents.sort(key=lambda c: (c.source, c.page, c.chunk_index), reverse=position == "last")
            # Priorizar el indice ordenado sin cambiar la puntuacion coseno real.
            selected = {c.id for c in contents}
            evidence = contents + [c for c in evidence if c.id not in selected]
        if metadata_citation:
            evidence = [metadata_citation] + evidence
        evidence = evidence[:top_k]
        if not evidence:
            return abstain("Ningún fragmento supera el umbral de similitud.", retrieved)
        # Numeración continua para que [n] corresponda exactamente a lo mostrado.
        evidence = [c.model_copy(update={"index": n}) for n, c in enumerate(evidence, 1)]
        return generate_answer(self.provider, question, evidence)
