import chromadb

from app.config import Settings
from app.errors import RagError
from app.schemas import Citation


class ChromaStore:
    def __init__(self, settings: Settings):
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        expected = {
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "hnsw:space": "cosine",
        }
        self.collection = self.client.get_or_create_collection(
            settings.collection_name, embedding_function=None, metadata=expected,
        )
        if any((self.collection.metadata or {}).get(key) != value for key, value in expected.items()):
            raise RagError("La colección usa otra configuración de embeddings o chunks. Usa otro COLLECTION_NAME y reindexa.", 503)

    def count(self) -> int:
        return self.collection.count()

    def documents(self) -> list[dict]:
        records = self.collection.get(include=["metadatas"])
        sources = {}
        for meta in records["metadatas"] or []:
            sources.setdefault(meta["source"], {"source": meta["source"], "chunks": 0})["chunks"] += 1
        return sorted(sources.values(), key=lambda item: item["source"])

    def unchanged(self, source: str, fingerprint: str) -> bool:
        records = self.collection.get(where={"source": source}, include=["metadatas"])
        return bool(records["ids"]) and all(meta.get("fingerprint") == fingerprint for meta in records["metadatas"])

    def delete_source(self, source: str) -> int:
        records = self.collection.get(where={"source": source}, include=[])
        if not records["ids"]:
            return 0
        self.collection.delete(where={"source": source})
        return len(records["ids"])

    def refresh_metadata(self, ids: list[str], metadata: list[dict]):
        batch_size = self.client.get_max_batch_size()
        for start in range(0, len(ids), batch_size):
            self.collection.update(ids=ids[start:start + batch_size], metadatas=metadata[start:start + batch_size])

    def pdf_page_count(self, source: str) -> int | None:
        records = self.collection.get(where={"source": source}, include=["metadatas"])
        metadata = records["metadatas"] or []
        counts = {meta.get("pdf_page_count") for meta in metadata}
        if len(counts) != 1 or not metadata:
            return None
        count = counts.pop()
        return count if isinstance(count, int) and count > 0 else None

    def contents(self, vector: list[float], top_k: int, source: str | None = None) -> list[Citation]:
        where = {"$and": [{"is_contents": True}, {"source": source}]} if source else {"is_contents": True}
        count = len(self.collection.get(where=where, include=[])["ids"])
        return self._search(vector, min(top_k, count), where) if count else []

    def replace(self, source, ids, texts, vectors, metadata):
        old = self.collection.get(where={"source": source}, include=[])["ids"]
        batch_size = self.client.get_max_batch_size()
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            self.collection.upsert(ids=ids[start:end], documents=texts[start:end],
                                   embeddings=vectors[start:end], metadatas=metadata[start:end])
        stale = sorted(set(old) - set(ids))
        if stale:
            self.collection.delete(ids=stale)

    def search(self, vector: list[float], top_k: int, source: str | None = None) -> list[Citation]:
        count = self.count()
        if not count:
            return []
        return self._search(vector, min(top_k, count), {"source": source} if source else None)

    def _search(self, vector: list[float], top_k: int, where: dict | None = None) -> list[Citation]:
        args = {"where": where} if where else {}
        result = self.collection.query(query_embeddings=[vector], n_results=top_k,
                                       include=["documents", "metadatas", "distances"], **args)
        return [Citation(index=n + 1, id=id_, source=meta["source"], text=text,
                         score=round(max(-1.0, min(1.0, 1 - float(distance))), 6),
                         page=meta["page"], chunk_index=meta["chunk_index"])
                for n, (id_, text, meta, distance) in enumerate(zip(
                    result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]))]
