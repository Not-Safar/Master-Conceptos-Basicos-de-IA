import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, load_settings
from app.documents import MAX_BYTES, parse_document, resolve_paths
from app.embed import GoogleProvider
from app.errors import RagError
from app.schemas import DeleteDocumentRequest, DeleteDocumentResponse, QueryRequest, QueryResponse
from app.service import RagService
from app.store import ChromaStore


def create_app(settings: Settings | None = None, service: RagService | None = None):
    @asynccontextmanager
    async def lifespan(api):
        config = settings or load_settings()
        api.state.settings = config
        api.state.startup_error = None
        try:
            api.state.service = service or RagService(config, ChromaStore(config), GoogleProvider(config))
        except RagError as exc:
            api.state.service = None
            api.state.startup_error = exc.message
        yield
        if api.state.service:
            api.state.service.provider.close()

    api = FastAPI(title="Aula RAG · Consulta con evidencia", version="1.0.0", lifespan=lifespan)
    api.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])

    @api.exception_handler(RagError)
    async def handle_rag_error(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    def get_service(request):
        if request.app.state.service is None:
            raise RagError(request.app.state.startup_error or "Índice no disponible.", 503)
        return request.app.state.service

    @api.get("/health", tags=["Estado"])
    def health(request: Request):
        service_ = request.app.state.service
        config = request.app.state.settings
        return {"status": "ok" if service_ else "degraded", "chroma_accessible": service_ is not None,
                "google_api_key_configured": bool(config.api_key),
                "total_chunks": service_.store.count() if service_ else 0,
                "documents": service_.store.documents() if service_ else [],
                "embedding_model": config.embedding_model, "embedding_dimensions": config.embedding_dimensions,
                "generation_model": config.generation_model, "min_score": config.min_score,
                "error": request.app.state.startup_error}

    @api.post("/ingest", tags=["Documentos"])
    async def ingest(request: Request, files: list[UploadFile] | None = File(default=None),
                     paths: str | None = Form(default=None, description='Lista JSON de rutas relativas a data/, por ejemplo ["."]')):
        service_ = get_service(request)
        documents = []
        if files and len(files) > 50:
            raise RagError("Máximo 50 archivos por petición.", 413)
        for upload in files or []:
            # Descarta directorios que el navegador haya incluido en el nombre.
            filename = (upload.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
            documents.append(parse_document("uploads/" + filename, await upload.read(MAX_BYTES + 1)))
        if paths:
            try:
                values = json.loads(paths)
                if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                    raise ValueError
            except (ValueError, TypeError):
                raise RagError("paths debe ser una lista JSON de cadenas.") from None
            resolved = resolve_paths(values, service_.settings.data_path)
            if len(resolved) + len(documents) > 50:
                raise RagError("Máximo 50 documentos por petición.", 413)
            for path in resolved:
                if path.stat().st_size > MAX_BYTES:
                    raise RagError(f"{path.name}: excede 10 MiB.", 413)
                source = "data/" + path.relative_to(service_.settings.data_path.resolve()).as_posix()
                documents.append(parse_document(source, path.read_bytes()))
        return await run_in_threadpool(service_.ingest, documents)

    @api.post("/query", response_model=QueryResponse, tags=["Consulta"])
    def query(request: Request, body: QueryRequest):
        return get_service(request).query(body)

    @api.delete("/documents", response_model=DeleteDocumentResponse, tags=["Documentos"],
                summary="Eliminar un archivo del índice",
                description="Elimina los fragmentos, embeddings y metadatos del origen exacto indicado. Conserva los archivos originales y los demás documentos; no llama a Google.")
    def delete_document(request: Request, body: DeleteDocumentRequest):
        return get_service(request).delete_document(body.source)

    return api


app = create_app()
