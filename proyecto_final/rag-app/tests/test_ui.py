from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def test_ui_renders_missing_key_and_empty_corpus():
    health = {"status": "ok", "chroma_accessible": True, "google_api_key_configured": False,
              "documents": [], "total_chunks": 0, "embedding_model": "gemini-embedding-001",
              "generation_model": "gemini-3.5-flash-lite", "min_score": 0.35, "error": None}
    class Response:
        is_error = False
        def json(self):
            return health
    target = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    with patch("httpx.request", return_value=Response()):
        app = AppTest.from_file(str(target)).run(timeout=20)
    assert not app.exception
    assert any("GOOGLE_API_KEY" in item.value for item in app.warning)
    assert any("vacía" in item.value for item in app.info)
    assert any(title.value == "Pregunta. Encuentra. Verifica." for title in app.title)


def test_ui_displays_file_metadata_citation_without_a_similarity_score():
    health = {"status": "ok", "chroma_accessible": True, "google_api_key_configured": True,
              "documents": [{"source": "uploads/cuentos.pdf", "chunks": 1}], "total_chunks": 1,
              "embedding_model": "gemini-embedding-001", "generation_model": "gemini-3.5-flash-lite",
              "min_score": 0.35, "error": None}
    class Response:
        is_error = False
        def json(self):
            return health
    result = {"answer": "El PDF tiene 3 páginas [1].", "abstained": False, "reason": None,
              "citations": [{"index": 1, "id": "metadata:test", "source": "uploads/cuentos.pdf",
                             "kind": "document_metadata", "score": None, "page": None,
                             "chunk_index": None, "text": "El PDF tiene 3 páginas, incluidas las vacías."}]}
    target = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    with patch("httpx.request", return_value=Response()):
        app = AppTest.from_file(str(target)).run(timeout=20)
        app.session_state["messages"] = [{"role": "assistant", "result": result}]
        app.run(timeout=20)
    assert not app.exception
    assert any("metadatos del archivo" in expander.label for expander in app.expander)


def test_ui_sends_six_completed_turns_and_clear_removes_context():
    health = {"chroma_accessible": True, "google_api_key_configured": True,
              "documents": [{"source": "uploads/cuentos.pdf", "chunks": 1}], "total_chunks": 1,
              "embedding_model": "gemini-embedding-001", "generation_model": "gemini-3.5-flash-lite",
              "min_score": 0.35, "error": None}
    result = {"answer": "Respuesta con fuente [1].", "abstained": False, "citations": [],
              "resolved_question": "¿Cuántas páginas tiene el PDF de cuentos?"}
    payloads = []
    class Response:
        is_error = False
        def __init__(self, value):
            self.value = value
        def json(self):
            return self.value
    def request(method, url, **kwargs):
        if method == "POST":
            payloads.append(kwargs["json"])
            return Response(result)
        return Response(health)
    target = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    with patch("httpx.request", side_effect=request):
        app = AppTest.from_file(str(target)).run(timeout=20)
        messages = []
        for n in range(8):
            messages.extend([{"role": "user", "content": f"Pregunta {n}", "resolved_question": f"Pregunta completa {n}"},
                             {"role": "assistant", "result": result}])
        # Un envío fallido no debe convertirse en un turno de contexto.
        messages.append({"role": "user", "content": "Pregunta sin respuesta"})
        app.session_state["messages"] = messages
        app.chat_input[0].set_value("¿Y cuántas páginas tiene?").run(timeout=20)
        assert not app.exception
        history = payloads[-1]["history"]
        assert len(history) == 12
        assert history[0]["content"] == "Pregunta completa 2"
        assert history[-2]["content"] == "Pregunta completa 7"
        assert any(e.label == "Pregunta interpretada con el contexto" for e in app.expander)
        next(b for b in app.button if b.label == "Limpiar conversación").click().run(timeout=20)
        app.chat_input[0].set_value("Nueva pregunta").run(timeout=20)
        assert payloads[-1]["history"] == []


def test_ui_does_not_mix_context_between_document_filters():
    health = {"chroma_accessible": True, "google_api_key_configured": True,
              "documents": [{"source": "uploads/cuentos.pdf", "chunks": 1}], "total_chunks": 1,
              "embedding_model": "gemini-embedding-001", "generation_model": "gemini-3.5-flash-lite",
              "min_score": 0.35, "error": None}
    result = {"answer": "Respuesta [1].", "abstained": False, "citations": []}
    payloads = []
    class Response:
        is_error = False
        def __init__(self, value):
            self.value = value
        def json(self):
            return self.value
    def request(method, url, **kwargs):
        if method == "POST":
            payloads.append(kwargs["json"])
            return Response(result)
        return Response(health)
    target = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    with patch("httpx.request", side_effect=request):
        app = AppTest.from_file(str(target)).run(timeout=20)
        app.chat_input[0].set_value("Pregunta sobre todos").run(timeout=20)
        next(s for s in app.selectbox if s.label == "Buscar en").select("uploads/cuentos.pdf").run(timeout=20)
        app.chat_input[0].set_value("Pregunta sobre un PDF").run(timeout=20)
        assert not app.exception
        assert payloads[-1]["source"] == "uploads/cuentos.pdf"
        assert payloads[-1]["history"] == []
        app.chat_input[0].set_value("¿Y ese cuento?").run(timeout=20)
        assert payloads[-1]["history"] == [
            {"role": "user", "content": "Pregunta sobre un PDF"},
            {"role": "assistant", "content": "Respuesta [1]."}]


def test_ui_deletion_requires_confirmation_refreshes_library_and_resets_only_context():
    health = {"chroma_accessible": True, "google_api_key_configured": True,
              "documents": [{"source": "uploads/cuentos.pdf", "chunks": 3}], "total_chunks": 3,
              "embedding_model": "gemini-embedding-001", "generation_model": "gemini-3.8-flash",
              "min_score": 0.35, "error": None}
    result = {"answer": "Un cuento [1].", "abstained": False, "citations": []}
    deletions, queries = [], []
    class Response:
        is_error = False
        def __init__(self, value):
            self.value = value
        def json(self):
            return self.value
    def request(method, url, **kwargs):
        if method == "DELETE":
            deletions.append(kwargs["json"])
            health["documents"] = []
            health["total_chunks"] = 0
            return Response({"source": "uploads/cuentos.pdf", "chunks_deleted": 3, "total_chunks": 0})
        if method == "POST":
            queries.append(kwargs["json"])
            return Response(result)
        return Response(health)
    target = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    with patch("httpx.request", side_effect=request):
        app = AppTest.from_file(str(target)).run(timeout=20)
        app.session_state["messages"] = [{"role": "user", "content": "Pregunta anterior"},
                                         {"role": "assistant", "result": result}]
        next(b for b in app.button if b.label == "Eliminar del índice").click().run(timeout=20)
        assert deletions == []
        assert any("Selecciona el archivo" in w.value for w in app.warning)
        next(s for s in app.selectbox if s.label == "Archivo a eliminar").select("uploads/cuentos.pdf")
        next(b for b in app.button if b.label == "Eliminar del índice").click().run(timeout=20)
        assert deletions == []
        assert any("Marca la confirmación" in w.value for w in app.warning)
        next(s for s in app.selectbox if s.label == "Archivo a eliminar").select("uploads/cuentos.pdf")
        app.checkbox[0].check()
        next(b for b in app.button if b.label == "Eliminar del índice").click().run(timeout=20)
        assert not app.exception
        assert deletions == [{"source": "uploads/cuentos.pdf"}]
        assert any("3 fragmentos" in s.value for s in app.success)
        assert len(app.session_state["messages"]) == 2
        assert app.session_state["context_start"] == 2
        assert app.selectbox[0].options == ["Todos los documentos"]
        assert any("No hay archivos indexados" in c.value for c in app.caption)
        app.chat_input[0].set_value("Nueva pregunta").run(timeout=20)
        assert queries[-1]["history"] == []


def test_ui_failed_deletion_keeps_the_conversation_context():
    health = {"chroma_accessible": True, "google_api_key_configured": True,
              "documents": [{"source": "uploads/cuentos.pdf", "chunks": 1}], "total_chunks": 1,
              "embedding_model": "gemini-embedding-001", "generation_model": "gemini-3.8-flash",
              "min_score": 0.35, "error": None}
    class Response:
        def __init__(self, value, status=200):
            self.value, self.status_code = value, status
            self.is_error = status >= 400
        def json(self):
            return self.value
    def request(method, url, **kwargs):
        return Response({"detail": "No se pudo eliminar."}, 503) if method == "DELETE" else Response(health)
    target = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    with patch("httpx.request", side_effect=request):
        app = AppTest.from_file(str(target)).run(timeout=20)
        app.session_state["messages"] = [{"role": "user", "content": "Pregunta"}]
        next(s for s in app.selectbox if s.label == "Archivo a eliminar").select("uploads/cuentos.pdf")
        app.checkbox[0].check()
        next(b for b in app.button if b.label == "Eliminar del índice").click().run(timeout=20)
        assert not app.exception
        assert any("No se pudo eliminar" in e.value for e in app.error)
        assert len(app.session_state["messages"]) == 1
        assert "context_start" not in app.session_state
