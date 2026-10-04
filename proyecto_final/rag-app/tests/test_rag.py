import json
import hashlib
import subprocess
import sys
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.chunk import chunk_text
from app.config import Settings
from app.documents import Document, Page, parse_document
from app.embed import GoogleProvider
from app.errors import RagError
from app.main import create_app
from app.service import RagService
from app.schemas import ResolvedQuestion
from app.store import ChromaStore


class FakeProvider:
    """Doble exclusivo de tests. No existe un modo simulado en producción."""
    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.generation_calls = 0
        self.prompts = []
        self.rewrite_output = None
        self.output = {"answer": "El solapamiento conserva contexto [1].", "abstained": False, "citation_indices": [1]}
        self.client = SimpleNamespace(models=SimpleNamespace(generate_content=self.generate))

    def embed(self, texts, query=False):
        self.calls.append((texts, query))
        return [[0.0, 1.0] if query and "ajena" in text else [1.0, 0.0] for text in texts]

    def generate(self, **kwargs):
        self.generation_calls += 1
        self.prompt = kwargs
        self.prompts.append(kwargs)
        if kwargs["config"].response_schema is ResolvedQuestion:
            output = self.rewrite_output if self.rewrite_output is not None else {"question": json.loads(kwargs["contents"])["question"]}
        else:
            output = self.output
        return SimpleNamespace(text=json.dumps(output))

    def call(self, operation):
        return operation()

    def close(self):
        pass


@pytest.fixture
def system(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    settings = Settings(api_key="test-only", chroma_path=tmp_path / "chroma", data_path=data,
                        chunk_size=50, chunk_overlap=10)
    provider = FakeProvider(settings)
    service = RagService(settings, ChromaStore(settings), provider)
    with TestClient(create_app(settings, service)) as client:
        yield client, service, provider


def upload(client, name="apunte.md", text=None):
    text = text or " ".join(f"palabra{n}" for n in range(121))
    return client.post("/ingest", files=[("files", (name, text.encode(), "text/markdown"))])


def test_chunking_covers_words_and_exact_overlap():
    words = [str(n) for n in range(125)]
    chunks = chunk_text(" ".join(words), 50, 10)
    assert [(c.start_word, c.end_word) for c in chunks] == [(0, 50), (40, 90), (80, 125)]
    for left, right in zip(chunks, chunks[1:]):
        assert left.text.split()[-10:] == right.text.split()[:10]
    assert chunk_text("  ") == []
    with pytest.raises(ValueError):
        chunk_text("texto", 10, 10)


def test_empty_index_abstains_without_calling_google(system):
    client, _, provider = system
    response = client.post("/query", json={"question": "¿Qué es IA?"})
    assert response.status_code == 200
    assert response.json()["abstained"]
    assert provider.calls == []


@pytest.mark.parametrize("payload", [{"question": "   "}, {"question": "hola", "top_k": 0}, {"question": "hola", "top_k": 11}])
def test_invalid_questions(system, payload):
    client, _, _ = system
    assert client.post("/query", json=payload).status_code == 422


def test_ingest_query_sources_and_no_duplicate_vectors(system):
    client, service, provider = system
    result = upload(client)
    assert result.status_code == 200
    assert result.json()["documents_indexed"] == 1
    assert result.json()["chunks_indexed"] == 3
    calls = len(provider.calls)
    assert upload(client).json()["documents_skipped"] == ["uploads/apunte.md"]
    assert len(provider.calls) == calls
    response = client.post("/query", json={"question": "¿Por qué solapar?", "top_k": 2})
    answer = response.json()
    assert response.status_code == 200
    assert not answer["abstained"]
    assert "[1]" in answer["answer"]
    assert len(answer["citations"]) == 2
    assert answer["citations"][0]["source"] == "uploads/apunte.md"
    assert answer["citations"][0]["score"] == pytest.approx(1)
    assert provider.calls[-1][1] is True
    prompt = json.loads(provider.prompt["contents"])
    assert len(prompt["evidence"]) == 2
    assert prompt["evidence"][0]["index"] == 1
    assert service.store.count() == 3


def test_replace_removes_obsolete_chunks(system):
    client, service, _ = system
    upload(client)
    response = upload(client, text="Contenido nuevo y corto.")
    assert response.json()["chunks_indexed"] == 1
    assert service.store.count() == 1
    assert service.store.collection.get(include=["documents"])["documents"] == ["Contenido nuevo y corto."]


def test_persistence_across_new_client(system):
    client, service, _ = system
    upload(client)
    reopened = ChromaStore(service.settings)
    assert reopened.count() == 3
    assert reopened.documents() == [{"source": "uploads/apunte.md", "chunks": 3}]
    hits = reopened.search([1.0, 0.0], 2)
    assert hits[0].source == "uploads/apunte.md"


def test_persistence_is_readable_in_a_separate_process(system):
    client, service, _ = system
    upload(client)
    config = service.settings.model_dump_json()
    code = "from app.config import Settings; from app.store import ChromaStore; import sys; print(ChromaStore(Settings.model_validate_json(sys.argv[1])).count())"
    result = subprocess.run([sys.executable, "-c", code, config], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "3"


def test_incompatible_collection_configuration_rejected(system):
    _, service, _ = system
    with pytest.raises(RagError, match="otra configuración"):
        ChromaStore(service.settings.model_copy(update={"embedding_dimensions": 1536}))


def test_low_score_abstains_without_generation(system):
    client, _, provider = system
    upload(client)
    result = client.post("/query", json={"question": "Pregunta ajena"}).json()
    assert result["abstained"]
    assert "umbral" in result["reason"]
    assert provider.generation_calls == 0


def test_semantic_abstention_even_with_high_score(system):
    client, _, provider = system
    upload(client)
    provider.output = {"answer": "No sé, quizá 1234", "abstained": True, "citation_indices": []}
    result = client.post("/query", json={"question": "¿Cuál es la contraseña?"}).json()
    assert result["abstained"]
    assert "1234" not in result["answer"]
    assert provider.generation_calls == 1


@pytest.mark.parametrize("output", [
    {"answer": "Una respuesta sin citas.", "abstained": False, "citation_indices": []},
    {"answer": "Cita inventada [99].", "abstained": False, "citation_indices": [99]},
    {"answer": "Referencia inconsistente [1].", "abstained": False, "citation_indices": [2]},
    {"otro": "formato"},
])
def test_invalid_generation_fails_closed(system, output):
    client, _, provider = system
    upload(client)
    provider.output = output
    assert client.post("/query", json={"question": "pregunta"}).json()["abstained"]


def test_structured_citations_are_rendered_when_inline_markers_are_missing(system):
    client, _, provider = system
    upload(client)
    provider.output = {"answer": "El título del primer cuento es Un cuento de ejemplo.",
                       "abstained": False, "citation_indices": [2, 2]}
    result = client.post("/query", json={"question": "¿Cuál es el primer cuento?"}).json()
    assert not result["abstained"]
    assert result["answer"] == "El título del primer cuento es Un cuento de ejemplo. [2]"
    assert result["citations"][1]["index"] == 2


@pytest.mark.parametrize("marker", ["[1, 2]", "[1; 2]"])
def test_grouped_references_keep_their_valid_source_numbers(system, marker):
    client, _, provider = system
    upload(client)
    provider.output = {"answer": f"Explicación con dos fuentes {marker}.",
                       "abstained": False, "citation_indices": [1, 2]}
    result = client.post("/query", json={"question": "pregunta"}).json()
    assert not result["abstained"]
    assert result["answer"] == "Explicación con dos fuentes [1] [2]."


@pytest.mark.parametrize("indices", [[], [99], [0], [-1]])
def test_missing_inline_citations_never_allow_missing_or_unknown_sources(system, indices):
    client, _, provider = system
    upload(client)
    provider.output = {"answer": "Una afirmación sin referencias.", "abstained": False, "citation_indices": indices}
    assert client.post("/query", json={"question": "pregunta"}).json()["abstained"]


def test_source_filter(system):
    client, _, provider = system
    upload(client, "uno.md")
    upload(client, "dos.md")
    result = client.post("/query", json={"question": "pregunta", "source": "uploads/dos.md"}).json()
    assert {c["source"] for c in result["citations"]} == {"uploads/dos.md"}
    calls = len(provider.calls)
    result = client.post("/query", json={"question": "pregunta", "source": "inexistente"}).json()
    assert result["abstained"]
    assert len(provider.calls) == calls


def test_missing_key_returns_visible_service_error(system):
    client, service, _ = system
    service.provider = GoogleProvider(service.settings.model_copy(update={"api_key": ""}))
    response = upload(client)
    assert response.status_code == 503
    assert "GOOGLE_API_KEY" in response.json()["detail"]
    assert service.store.count() == 0


def test_paths_and_unsupported_documents(system):
    client, service, _ = system
    (service.settings.data_path / "local.md").write_text("Un apunte de prueba", encoding="utf-8")
    assert client.post("/ingest", data={"paths": '["."]'}).json()["documents_indexed"] == 1
    assert client.post("/ingest", data={"paths": '["../"]'}).status_code == 400
    assert client.post("/ingest", data={"paths": '"no es lista"'}).status_code == 400
    assert upload(client, "mal.csv").status_code == 400
    assert upload(client, text="  \n ").status_code == 400
    assert client.post("/ingest").status_code == 400


def test_duplicate_source_rejected_before_embedding(system):
    client, _, provider = system
    response = client.post("/ingest", files=[("files", ("x.md", b"uno")), ("files", ("x.md", b"dos"))])
    assert response.status_code == 400
    assert provider.calls == []


def test_failed_embedding_batch_does_not_write(system):
    client, service, provider = system
    def fail(texts, query=False):
        raise RagError("Cuota agotada", 429)
    provider.embed = fail
    assert upload(client).status_code == 429
    assert service.store.count() == 0


def test_pdf_without_text_is_rejected():
    pdf = PdfWriter()
    pdf.add_blank_page(width=200, height=200)
    target = BytesIO()
    pdf.write(target)
    with pytest.raises(RagError, match="sin texto"):
        parse_document("vacio.pdf", target.getvalue())


def test_openapi_contains_required_endpoints(system):
    client, _, _ = system
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert {"/health", "/ingest", "/query"} <= schema["paths"].keys()
    health = client.get("/health").json()
    assert health["chroma_accessible"]
    assert "api_key" not in health


def test_google_embedding_task_types_and_normalization():
    settings = Settings(api_key="test-only", embedding_dimensions=128)
    provider = GoogleProvider(settings)
    captured = []
    def embed_content(**kwargs):
        captured.append(kwargs)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[3.0, 4.0] + [0.0] * 126) for _ in kwargs["contents"]])
    provider._client = SimpleNamespace(models=SimpleNamespace(embed_content=embed_content))
    doc = provider.embed(["documento"])[0]
    query = provider.embed(["pregunta"], query=True)[0]
    assert doc[:2] == pytest.approx([0.6, 0.8])
    assert query == doc
    assert captured[0]["model"] == captured[1]["model"] == "gemini-embedding-001"
    assert captured[0]["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert captured[1]["config"].task_type == "RETRIEVAL_QUERY"


def test_first_story_uses_contents_even_outside_top_four_semantic_hits(system):
    client, service, provider = system
    original_embed = provider.embed
    def ranked_embed(texts, query=False):
        original_embed(texts, query)
        return [[0.6, 0.8] if not query and text.startswith("ÍNDICE") else [1.0, 0.0] for text in texts]
    provider.embed = ranked_embed
    pages = [Page("ÍNDICE 1. El cuento inicial .......... 8 2. Otro cuento .......... 10", 1)]
    pages.extend(Page(f"Una explicación sobre cuentos y personajes {n}.", n) for n in range(2, 10))
    service.ingest([Document("uploads/cuentos.pdf", pages)])
    assert not any(c.text.startswith("ÍNDICE") for c in service.store.search([1.0, 0.0], 4))
    provider.output = {"answer": "El primer cuento es El cuento inicial.", "abstained": False, "citation_indices": [1]}
    result = client.post("/query", json={"question": "cual es el primer cuento?", "top_k": 4}).json()
    assert not result["abstained"]
    assert len(result["citations"]) == 4
    assert result["citations"][0]["text"].startswith("ÍNDICE")
    assert result["citations"][0]["score"] == pytest.approx(0.6)
    assert "[1]" in result["answer"]


def test_pdf_page_count_includes_trailing_pages_without_text(system):
    client, service, provider = system
    service.ingest([Document("uploads/cuentos.pdf", [Page("Un cuento breve.", 1), Page("", 2), Page("", 3)])])
    assert service.store.count() == 1
    assert service.store.pdf_page_count("uploads/cuentos.pdf") == 3
    provider.output = {"answer": "El PDF tiene 3 páginas.", "abstained": False, "citation_indices": [1]}
    result = client.post("/query", json={"question": "cuantas paginas tiene el pdf?", "top_k": 4}).json()
    assert not result["abstained"]
    assert result["citations"][0]["kind"] == "document_metadata"
    assert result["citations"][0]["score"] is None
    assert "3" in result["citations"][0]["text"]
    assert "incluye páginas sin texto" in result["citations"][0]["text"]
    assert provider.calls[-1][1] is True


def test_reingestion_upgrades_legacy_metadata_without_new_embeddings(system):
    client, service, provider = system
    source = "uploads/antiguo.pdf"
    pages = [Page("Texto breve.", 1), Page("", 2)]
    fingerprint = hashlib.sha256("\n".join(p.text for p in pages).encode()).hexdigest()
    id_ = hashlib.sha256(f"{source}:{fingerprint}:1:0".encode()).hexdigest()
    service.store.collection.add(ids=[id_], documents=[pages[0].text], embeddings=[[1.0, 0.0]],
        metadatas=[{"source": source, "page": 1, "chunk_index": 0, "fingerprint": fingerprint}])
    before = client.post("/query", json={"question": "¿Cuántas páginas tiene el PDF?"}).json()
    assert before["abstained"]
    assert "Vuelve a indexarlo" in before["reason"]
    assert provider.calls == []
    assert service.store.pdf_page_count(source) is None
    result = service.ingest([Document(source, pages)])
    assert result["documents_skipped"] == [source]
    assert provider.calls == []
    assert service.store.count() == 1
    assert service.store.pdf_page_count(source) == 2


def test_page_count_requires_a_source_when_multiple_pdfs_are_indexed(system):
    client, service, provider = system
    service.ingest([Document("uploads/uno.pdf", [Page("Un texto.", 1)]),
                    Document("uploads/dos.pdf", [Page("Otro texto.", 1), Page("", 2)])])
    calls = len(provider.calls)
    result = client.post("/query", json={"question": "¿Cuántas páginas tiene el PDF?"}).json()
    assert result["abstained"]
    assert "Selecciona" in result["reason"]
    assert len(provider.calls) == calls
    provider.output = {"answer": "El PDF tiene 2 páginas.", "abstained": False, "citation_indices": [1]}
    result = client.post("/query", json={"question": "¿Cuántas páginas tiene el PDF?", "source": "uploads/dos.pdf"}).json()
    assert not result["abstained"]
    assert result["citations"][0]["source"] == "uploads/dos.pdf"


def test_structural_detection_does_not_treat_vector_index_prose_as_a_table_of_contents():
    from app.retrieval import contents_text, page_count_question
    assert not contents_text("Chroma conserva un índice vectorial con metadatos.")
    assert contents_text("24. Un cuento .... 60 25. Otro cuento .... 62 26. Más cuentos .... 64")
    assert not page_count_question("¿Cuántas páginas tiene el primer cuento?")


def test_followup_rewrites_before_retrieval_and_never_uses_history_as_evidence(system):
    client, service, provider = system
    service.ingest([Document("uploads/cuentos.pdf", [Page("Un cuento.", 1), Page("", 2)])])
    provider.rewrite_output = {"question": "¿Cuántas páginas tiene el PDF de cuentos?"}
    provider.output = {"answer": "El PDF tiene 2 páginas [1].", "abstained": False, "citation_indices": [1]}
    history = [{"role": "user", "content": "¿Cuál es el primer cuento del PDF?"},
               {"role": "assistant", "content": "Respuesta anterior no verificada: tiene 999 páginas [99]."}]
    result = client.post("/query", json={"question": "¿Y cuántas páginas tiene?", "history": history}).json()
    assert not result["abstained"]
    assert result["resolved_question"] == provider.rewrite_output["question"]
    assert provider.calls[-1] == ([result["resolved_question"]], True)
    rewrite, answer = [json.loads(p["contents"]) for p in provider.prompts]
    assert rewrite["history"] == history
    assert "history" not in answer
    assert "999" not in provider.prompts[-1]["contents"]
    assert result["citations"][0]["kind"] == "document_metadata"
    assert "2" in result["citations"][0]["text"]


def test_followup_still_abstains_when_new_evidence_is_insufficient(system):
    client, _, provider = system
    upload(client)
    provider.rewrite_output = {"question": "¿Cuál es la contraseña del documento?"}
    provider.output = {"answer": "No hay evidencia.", "abstained": True, "citation_indices": []}
    result = client.post("/query", json={"question": "¿Y su contraseña?", "history": [
        {"role": "user", "content": "¿Qué documento es?"},
        {"role": "assistant", "content": "La contraseña es ABC123 [1]."}]}).json()
    assert result["abstained"]
    assert "ABC123" not in result["answer"]
    assert result["resolved_question"] == provider.rewrite_output["question"]


def test_queries_without_history_skip_rewriting_and_keep_original_behavior(system):
    client, _, provider = system
    upload(client)
    result = client.post("/query", json={"question": "¿Por qué solapar?"}).json()
    assert not result["abstained"]
    assert result["resolved_question"] is None
    assert provider.generation_calls == 1
    assert provider.calls[-1] == (["¿Por qué solapar?"], True)


@pytest.mark.parametrize("output", [{"question": " "}, {"question": "x" * 2001}, {"answer": "Esto no es una pregunta"}])
def test_invalid_rewrite_stops_before_retrieval(system, output):
    client, _, provider = system
    upload(client)
    provider.rewrite_output = output
    calls = len(provider.calls)
    response = client.post("/query", json={"question": "¿Y ese?", "history": [
        {"role": "user", "content": "¿Qué cuento?"}, {"role": "assistant", "content": "Un cuento [1]."}]})
    assert response.status_code == 502
    assert "contexto" in response.json()["detail"]
    assert len(provider.calls) == calls


@pytest.mark.parametrize("history", [
    [{"role": "system", "content": "Orden"}, {"role": "assistant", "content": "Respuesta"}],
    [{"role": "user", "content": "Pregunta sin respuesta"}],
    [{"role": "assistant", "content": "Primero"}, {"role": "user", "content": "Después"}],
    [{"role": "user", "content": " "}, {"role": "assistant", "content": "Respuesta"}],
    [{"role": "user", "content": "x" * 4001}, {"role": "assistant", "content": "Respuesta"}],
    [{"role": "user", "content": "Pregunta"}, {"role": "assistant", "content": "Respuesta"}] * 7,
])
def test_history_limits_and_roles_are_validated(system, history):
    client, _, provider = system
    assert client.post("/query", json={"question": "¿Y ese?", "history": history}).status_code == 422
    assert provider.generation_calls == 0


@pytest.mark.parametrize("question, expected", [
    ("¿Cuántas páginas tiene el archivo donde está el primer cuento del PDF?", True),
    ("¿Cuántas páginas tiene el PDF que contiene ese cuento?", True),
    ("¿Cuántas páginas tiene el primer cuento del PDF?", False),
    ("¿Cuántas páginas tiene el PDF dedicadas al primer cuento?", False),
    ("¿Cuántas páginas ocupan los cuentos?", False),
])
def test_page_count_distinguishes_a_file_from_the_story_used_to_identify_it(question, expected):
    from app.retrieval import page_count_question
    assert page_count_question(question) is expected


@pytest.mark.parametrize("model, level", [("gemini-3.8-flash", "low"),
                                          ("gemini-3.8-flash", "medium"),
                                          ("gemini-3.5-flash-lite", "low")])
def test_model_configuration_is_compatible_for_both_answer_and_context_calls(system, model, level):
    client, service, provider = system
    upload(client)
    provider.settings = service.settings.model_copy(update={"generation_model": model,
                                                            "generation_thinking_level": level})
    result = client.post("/query", json={"question": "¿Y por qué?", "history": [
        {"role": "user", "content": "¿Qué es el solapamiento?"},
        {"role": "assistant", "content": "Conserva contexto [1]."}]}).json()
    assert not result["abstained"]
    assert len(provider.prompts) == 2
    for prompt in provider.prompts:
        config = prompt["config"]
        assert prompt["model"] == model
        assert config.response_mime_type == "application/json"
        if model == "gemini-3.8-flash":
            assert config.temperature is None and config.top_p is None and config.top_k is None
            assert config.thinking_config.thinking_level.value == level.upper()
        else:
            assert config.temperature == 0 and config.thinking_config is None


def test_delete_removes_only_the_exact_source_persists_and_preserves_original_file(system):
    client, service, provider = system
    original = service.settings.data_path / "mi apunte.md"
    original.write_text("Un apunte local que debe conservarse.", encoding="utf-8")
    assert client.post("/ingest", data={"paths": '["mi apunte.md"]'}).status_code == 200
    upload(client, "mi apunte.md")
    upload(client, "mi apunte.md.extra.md")
    before = service.store.count()
    calls = len(provider.calls)
    response = client.request("DELETE", "/documents", json={"source": "data/mi apunte.md"})
    assert response.status_code == 200
    assert response.json() == {"source": "data/mi apunte.md", "chunks_deleted": 1, "total_chunks": before - 1}
    assert original.read_text(encoding="utf-8") == "Un apunte local que debe conservarse."
    reopened = ChromaStore(service.settings)
    assert reopened.count() == before - 1
    assert {d["source"] for d in reopened.documents()} == {"uploads/mi apunte.md", "uploads/mi apunte.md.extra.md"}
    result = client.post("/query", json={"question": "Una pregunta", "source": "data/mi apunte.md"}).json()
    assert result["abstained"]
    assert len(provider.calls) == calls
    assert provider.generation_calls == 0
    assert client.request("DELETE", "/documents", json={"source": "data/mi apunte.md"}).status_code == 404
    assert service.store.count() == before - 1


def test_delete_last_pdf_clears_its_metadata_and_can_be_reindexed(system):
    client, service, provider = system
    doc = Document("uploads/cuentos.pdf", [Page("Un cuento breve.", 1), Page("", 2)])
    service.ingest([doc])
    calls = len(provider.calls)
    assert client.request("DELETE", "/documents", json={"source": doc.source}).json()["total_chunks"] == 0
    assert service.store.pdf_page_count(doc.source) is None
    health = client.get("/health").json()
    assert health["documents"] == [] and health["total_chunks"] == 0
    assert client.post("/query", json={"question": "¿Qué cuento hay?"}).json()["abstained"]
    assert len(provider.calls) == calls
    assert service.ingest([doc])["documents_indexed"] == 1
    assert service.store.pdf_page_count(doc.source) == 2


@pytest.mark.parametrize("payload, status", [({}, 422), ({"source": "   "}, 422),
                                             ({"source": "missing.pdf"}, 404)])
def test_invalid_deletion_never_removes_other_documents(system, payload, status):
    client, service, provider = system
    upload(client)
    count = service.store.count()
    calls = len(provider.calls)
    assert client.request("DELETE", "/documents", json=payload).status_code == status
    assert service.store.count() == count
    assert len(provider.calls) == calls


def test_cors_allows_document_deletion_from_the_ui(system):
    client, _, _ = system
    response = client.options("/documents", headers={"Origin": "http://127.0.0.1:8501",
                                                       "Access-Control-Request-Method": "DELETE"})
    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]
