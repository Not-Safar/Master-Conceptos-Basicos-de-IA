import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="Aula RAG · Consulta con evidencia", page_icon="📚", layout="wide")
# Los colores los gestiona el tema nativo de Streamlit (.streamlit/config.toml).
# No fijar fondos claros aquí: romperían el contraste al seleccionar Dark.
st.markdown("""<style>
.block-container { max-width: 1180px; padding-top: 3.4rem; }
h1 { font-size: clamp(1.9rem, 4vw, 2.8rem); letter-spacing: -.03em; line-height: 1.15; }
.hero-label { color: inherit; opacity: .8; font-size: .72rem; font-weight: 700; letter-spacing: .12em; line-height: 1.6; }
[data-testid="stBaseButton-primary"]:not(:disabled) { color: light-dark(#ffffff, #101722); }
</style>""", unsafe_allow_html=True)


def api_call(method, route, **kwargs):
    try:
        response = httpx.request(method, API_URL + route, timeout=httpx.Timeout(300, connect=5), **kwargs)
        if response.is_error:
            try:
                detail = response.json().get("detail", "Error de la API.")
            except ValueError:
                detail = "La API devolvió una respuesta inesperada."
            st.error(f"Error {response.status_code}: {detail}")
            return None
        return response.json()
    except httpx.ConnectError:
        st.error("No hay conexión con FastAPI. Inicia la API en el puerto 8000.")
    except httpx.TimeoutException:
        st.error("La petición agotó el tiempo de espera. Consulta el estado antes de repetir la ingestión.")
    except (httpx.HTTPError, ValueError):
        st.error("No se pudo obtener una respuesta válida de la API.")
    return None


def show_result(result):
    if result.get("resolved_question"):
        with st.expander("Pregunta interpretada con el contexto"):
            st.write(result["resolved_question"])
    if result["abstained"]:
        st.warning(result["answer"])
        st.caption(result.get("reason") or "Evidencia insuficiente.")
    else:
        st.markdown(result["answer"])
    if result["citations"]:
        label = "Fragmentos recuperados para inspección" if result["abstained"] else "Evidencia y fuentes"
        st.caption(label + " · La similitud coseno no es una probabilidad de certeza.")
        for cite in result["citations"]:
            score_label = f'similitud {cite["score"]:.3f}' if cite["score"] is not None else "metadatos del archivo"
            with st.expander(f'[{cite["index"]}] {cite["source"]} · {score_label}'):
                if cite.get("kind") == "document_metadata":
                    st.caption("Datos extraídos del PDF original. Esta fuente no tiene score de similitud.")
                else:
                    st.caption(f'Página {cite["page"]} · chunk {cite["chunk_index"] + 1} · ID {cite["id"][:12]}')
                st.text(cite["text"])


def conversation_history(messages, scope):
    """Enviar solo turnos completos del filtro actual, sin los textos de las fuentes."""
    turns, pending = [], None
    for message in messages:
        if message.get("scope", "Todos los documentos") != scope:
            pending = None
            continue
        if message["role"] == "user":
            pending = message
        elif pending is not None:
            turns.append([
                {"role": "user", "content": (pending.get("resolved_question") or pending["content"])[:4000]},
                {"role": "assistant", "content": message["result"]["answer"][:4000]},
            ])
            pending = None
    return [message for turn in turns[-6:] for message in turn]


with st.sidebar:
    st.title("📚 Aula RAG")
    st.caption("Tu biblioteca, con respuestas verificables.")
    st.divider()
    health = api_call("GET", "/health")
    ready = bool(health and health["chroma_accessible"])
    if health:
        if health["error"]:
            st.error(health["error"])
        elif ready:
            st.success("API e índice disponibles")
        if not health["google_api_key_configured"]:
            st.warning("Falta GOOGLE_API_KEY en .env. Guarda la clave y reinicia FastAPI.")
        col1, col2 = st.columns(2)
        col1.metric("Documentos", len(health["documents"]))
        col2.metric("Chunks", health["total_chunks"])
        st.caption("Embeddings: " + health["embedding_model"])
        st.caption("Generación: " + health["generation_model"])
        st.caption(f'Umbral mínimo: {health["min_score"]:.2f}')
    top_k = st.slider("Fragmentos a recuperar", 1, 10, 4)
    sources = [d["source"] for d in health["documents"]] if health else []
    source = st.selectbox("Buscar en", ["Todos los documentos", *sources])
    st.link_button("Documentación de la API ↗", API_URL + "/docs")
    if st.button("Actualizar estado", use_container_width=True):
        st.rerun()

st.markdown('<p class="hero-label">PROYECTO FINAL · INTELIGENCIA ARTIFICIAL</p>', unsafe_allow_html=True)
st.title("Pregunta. Encuentra. Verifica.")
st.markdown("Consulta tus documentos en español. Cada respuesta muestra los fragmentos que la sustentan.")
ask_tab, library_tab, guide_tab = st.tabs(["💬 Consultar", "📂 Biblioteca", "🧭 Cómo funciona"])

with ask_tab:
    if not health or not health["total_chunks"]:
        st.info("Tu biblioteca está vacía. Ve a Biblioteca e indexa el corpus de ejemplo o tus archivos.")
    with st.expander("Preguntas para probar"):
        st.write("• ¿Qué diferencia hay entre aprendizaje supervisado y no supervisado?")
        st.write("• ¿Por qué se utiliza solapamiento al dividir los documentos?")
        st.write("• ¿Cómo se evalúan la recuperación y las citas en un sistema RAG?")
        st.write("• ¿Cuál es la contraseña del WiFi del salón 302? → debe abstenerse.")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.caption("Contexto activo: hasta 6 turnos anteriores del mismo filtro de documentos, durante esta sesión.")
    if st.button("Limpiar conversación"):
        st.session_state.messages = []
        st.session_state["context_start"] = 0
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                show_result(message["result"])
    question = st.chat_input("Escribe una pregunta sobre tus documentos…", disabled=not ready)
    if question is not None:
        if not question.strip():
            st.warning("Escribe una pregunta antes de enviar.")
        else:
            context_start = st.session_state.get("context_start", 0)
            history = conversation_history(st.session_state.messages[context_start:], source)
            user_message = {"role": "user", "content": question, "scope": source}
            st.session_state.messages.append(user_message)
            with st.chat_message("user"):
                st.write(question)
            payload = {"question": question, "top_k": top_k, "history": history}
            if source != "Todos los documentos":
                payload["source"] = source
            with st.chat_message("assistant"):
                with st.spinner("Recuperando evidencia y preparando la respuesta…"):
                    result = api_call("POST", "/query", json=payload)
                if result:
                    show_result(result)
                    user_message["resolved_question"] = result.get("resolved_question") or question
                    st.session_state.messages.append({"role": "assistant", "result": result, "scope": source})

with library_tab:
    deletion = st.session_state.pop("delete_result", None)
    if deletion:
        st.success(f'Se eliminó {deletion["source"]} del índice: {deletion["chunks_deleted"]} fragmentos retirados.')
        st.info("El contexto del chat se reinició. Los mensajes anteriores siguen visibles.")
    st.subheader("Construye tu biblioteca")
    st.write("Carga PDF con texto, Markdown o TXT en UTF-8. Puedes reindexar un archivo con el mismo nombre.")
    files = st.file_uploader("Documentos", type=["pdf", "md", "txt"], accept_multiple_files=True)
    if st.button("Indexar archivos", disabled=not ready, type="primary"):
        if not files:
            st.warning("Selecciona al menos un archivo.")
        else:
            with st.spinner("Generando embeddings y guardando los fragmentos…"):
                result = api_call("POST", "/ingest", files=[("files", (f.name, f.getvalue(), f.type)) for f in files])
            if result:
                st.session_state["ingest_result"] = result
                st.rerun()
    st.divider()
    st.subheader("Corpus de ejemplo")
    st.write("Cinco apuntes originales sobre IA, aprendizaje, embeddings, arquitectura RAG y evaluación.")
    if st.button("Indexar los cinco documentos de ejemplo", disabled=not ready):
        with st.spinner("Indexando data/…"):
            result = api_call("POST", "/ingest", data={"paths": '["."]'})
        if result:
            st.session_state["ingest_result"] = result
            st.rerun()
    with st.expander("Usar una subcarpeta de data/"):
        folder = st.text_input("Ruta relativa en el servidor", placeholder="mis_apuntes")
        if st.button("Indexar carpeta", disabled=not ready):
            if not folder.strip():
                st.warning("Indica una carpeta dentro de data/.")
            else:
                import json
                with st.spinner("Indexando carpeta…"):
                    result = api_call("POST", "/ingest", data={"paths": json.dumps([folder.strip()])})
                if result:
                    st.session_state["ingest_result"] = result
                    st.rerun()
    if "ingest_result" in st.session_state:
        result = st.session_state["ingest_result"]
        st.success(f'{result["documents_indexed"]} documentos y {result["chunks_indexed"]} chunks indexados. '
                   f'{len(result["documents_skipped"])} documentos sin cambios omitidos.')
    if sources:
        st.dataframe(health["documents"], hide_index=True, use_container_width=True)
    st.divider()
    st.subheader("Eliminar un archivo indexado")
    st.write("Quita sus fragmentos y embeddings de la biblioteca. El archivo original se conserva; puedes volver a indexarlo.")
    st.caption("Al eliminar un archivo se reinicia el contexto del chat. Los mensajes anteriores siguen visibles.")
    if sources:
        with st.form("delete_document_form", clear_on_submit=True):
            delete_source = st.selectbox("Archivo a eliminar", sources, index=None, placeholder="Selecciona un archivo…")
            confirmed = st.checkbox("Confirmo que quiero quitar este archivo y todos sus fragmentos del índice.")
            submitted = st.form_submit_button("Eliminar del índice", disabled=not ready)
        if submitted:
            if not delete_source:
                st.warning("Selecciona el archivo que quieres eliminar.")
            elif not confirmed:
                st.warning("Marca la confirmación antes de eliminar el archivo del índice.")
            else:
                result = api_call("DELETE", "/documents", json={"source": delete_source})
                if result:
                    st.session_state["context_start"] = len(st.session_state.messages)
                    st.session_state["delete_result"] = result
                    st.session_state.pop("ingest_result", None)
                    st.rerun()
    else:
        st.caption("No hay archivos indexados para eliminar.")

with guide_tab:
    st.subheader("De una pregunta a una respuesta con fuentes")
    st.markdown("""
1. **Indexar:** FastAPI extrae el texto y lo divide en ventanas de 300 palabras con 60 de solapamiento.
2. **Representar:** Google AI convierte cada fragmento en un vector; ChromaDB lo conserva en disco.
3. **Entender y recuperar:** Gemini usa hasta seis turnos anteriores para reformular referencias como «ese cuento».
   La API vectoriza la pregunta interpretada y busca los fragmentos más similares.
4. **Responder:** Gemini recibe la pregunta y la evidencia numerada; responde en español con citas [n].
5. **Abstenerse:** si la similitud es baja o falta información en la evidencia, la respuesta indica que no puede responder.

Abre cada fuente para inspeccionar el texto y su similitud. Un score alto expresa cercanía semántica;
verificar que el fragmento respalda la afirmación sigue siendo parte de la evaluación.

El contexto dura durante esta sesión y se limita al mismo filtro de documentos. «Limpiar conversación» lo borra.
Puedes revisar la pregunta interpretada debajo de cada respuesta. Las respuestas anteriores ayudan a entender
la pregunta; la evidencia para responder procede de los documentos recuperados. Un seguimiento usa una llamada
adicional a Gemini. El contexto no reemplaza una revisión completa del documento para hacer conteos globales.
""")
