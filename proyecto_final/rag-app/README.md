# Aula RAG - proyecto final

Sistema de consulta documental en español con Streamlit, FastAPI, ChromaDB persistente y Google AI. Streamlit solo llama a la API por HTTP; FastAPI calcula embeddings, recupera evidencia y pide a Gemini una respuesta con citas.

## Estado verificado

- Corpus CC0: cinco documentos distintos, 3,926 palabras y 18 chunks indexados con Google.
- 68 pruebas locales aprobadas con Chroma real y un proveedor Google simulado exclusivo de tests.
- Evaluación real: tres preguntas del dominio respondidas con citas revisadas y dos abstenciones ante datos ausentes (cinco de cinco casos aprobados). Los resultados, errores del proveedor e intentos están en `evidence/evaluation.json`.
- Persistencia real: reiniciar únicamente FastAPI conservó los cinco documentos y 18 chunks; una consulta posterior respondió con fuentes sin reingestión (`evidence/persistence-check.json`).
- La configuración evaluada usa `gemini-embedding-001` y `gemini-3.8-flash`. Las evidencias documentan una muestra, no calidad garantizada para cualquier consulta.

## Instalación y arranque

Python 3.12 recomendado; versiones probadas en Windows con Python 3.12.14. Desde `rag-app/`, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Obtén tu clave en [Google AI Studio](https://aistudio.google.com/apikey) y completa `GOOGLE_API_KEY=` en `.env`. No se incluye ninguna clave en la entrega. Las variables de entorno tienen prioridad sobre `.env`. Si no dispones de `py`, usa `python -m venv .venv` con Python 3.12 instalado.

Inicia ambos servicios en segundo plano:

```powershell
.\start-app.ps1
```

O usa dos terminales:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Abre [Streamlit](http://127.0.0.1:8501/) y [OpenAPI](http://127.0.0.1:8000/docs). Tras modificar `.env`, ejecuta `.\restart-app.ps1`. El script valida los procesos del proyecto antes de reiniciarlos. Tras reiniciar Windows, inicia nuevamente los servicios. Los registros y PID locales están en `logs/`.

## Primera consulta

1. En **Biblioteca**, pulsa **Indexar los cinco documentos de ejemplo**. El ZIP no incluye el índice: se genera con tu propia clave.
2. Pregunta **¿Por qué se utiliza solapamiento al dividir los documentos?**
3. Abre la cita [1] y contrasta texto, archivo, posición y similitud con la respuesta.
4. Limpia la conversación y pregunta **¿Cuál es la contraseña del WiFi del salón 302?** Debe abstenerse.

Los textos originales están en `data/`; su licencia está en `CORPUS_LICENSE.md`. El corpus realmente ingerido produjo 18 chunks. Los documentos mencionan algunas preguntas imposibles como ejemplos, sin proporcionar los datos para responderlas.

## Arquitectura y archivos

```text
Streamlit :8501 -> HTTP -> FastAPI :8000
                           |-> Google AI: embeddings
                           |-> ChromaDB: persistencia y top-k
                           |-> Gemini: respuesta en español con citas
app/                      servicio, extracción, chunking, recuperación y generación
ui/streamlit_app.py        única interfaz, cliente HTTP
.streamlit/config.toml     tema y presentación
scripts/evaluate.py        evaluación real por HTTP
scripts/build_report.py    fuente para regenerar el PDF (requiere reportlab)
scripts/package_delivery.py empaquetado por lista de archivos permitidos
tests/                   pruebas locales (directorio tests/)
evidence/                 capturas y registros reales
REPORT.md                 contenido del informe
output/pdf/               reporte final de una página
requirements-lock.txt     versiones transitivas del entorno probado
```

## API

| Endpoint | Entrada | Resultado |
|---|---|---|
| `GET /health` | Ninguna | Estado, modelos, documentos y chunks; clave configurada como booleano |
| `POST /ingest` | Multipart: `files` repetido y/o `paths` como lista JSON | Documentos/chunks nuevos, documentos omitidos y total |
| `POST /query` | JSON con `question`; `top_k`, `source` e `history` opcionales | `answer`, `citations`, `abstained`, `reason`, `resolved_question` |
| `DELETE /documents` | JSON con `source` exacto | Origen, chunks eliminados y total restante |

Ejemplos en PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
curl.exe -X POST http://127.0.0.1:8000/ingest -F 'paths=["."]'

$questionBody = @{ question = '¿Por qué se utiliza solapamiento al dividir los documentos?'; top_k = 4 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($questionBody))
```

Las rutas están restringidas a `data/`. `paths=["."]` recorre sus TXT, MD y PDF. Los orígenes son `data/ruta.ext` o `uploads/nombre.ext`; dos cargas con el mismo nombre representan el mismo documento. Límite: 50 documentos y 10 MiB por archivo. PDF sin texto se rechazan; no se incluye OCR.

Una pregunta sin evidencia devuelve 200 y `abstained=true`; una entrada en blanco, 422. Clave ausente o permisos inválidos: 503; cuota agotada: 429; fallo del proveedor: 502. `/health` no llama a Google ni valida la clave. Un error del proveedor no equivale a abstención documental. CORS admite localhost:8501. Usa un solo proceso Uvicorn.

## Modelos y persistencia

- Embeddings: `gemini-embedding-001`, 768 dimensiones normalizadas, lotes de ocho. Documentos y preguntas usan el mismo modelo, con tareas RETRIEVAL_DOCUMENT y RETRIEVAL_QUERY.
- Generación: `.env.example` selecciona `gemini-3.8-flash`, probado en la evaluación. El valor por defecto del código, si no se configura, es `gemini-3.5-flash-lite`. El acceso y la cuota dependen de tu proyecto de Google.
- Gemini 3.8 omite temperature, top_p y top_k generativos; usa razonamiento low, medium o high. El top_k del endpoint controla vecinos, no muestreo del modelo.
- Chunking: 300 palabras y 60 de solapamiento, sin cruzar páginas PDF.
- Recuperación: cuatro vecinos por defecto, configurables entre uno y diez. Similitud = 1 - distancia coseno; no es certeza.
- Chroma: `chroma/`, colección `curso_ia`, sin embedder implícito. El ZIP excluye los vectores locales.

La colección registra modelo, dimensiones y parámetros de chunking. Cambiarlos requiere otra colección e ingestión nueva. Cambiar solo la generación no exige reindexar. El cliente de embeddings soporta explícitamente gemini-embedding-001; otra familia requiere adaptación.

Reingestar el mismo contenido y origen no duplica chunks ni pide embeddings. Al actualizar contenido se calculan los vectores antes de escribir. Un fallo de Google no escribe los documentos preparados; un fallo de disco puede dejar una actualización parcial, pues no hay transacción conjunta para varios archivos. Un bloqueo serializa las operaciones dentro del proceso.

## Abstención, citas y contexto

Se descartan vecinos con score menor a 0.35. Índice vacío, filtro vacío o ausencia de evidencia suficiente producen abstención. Gemini debe responder en español exclusivamente con los fragmentos numerados y abstenerse si no cubren toda la pregunta. La API valida referencias seleccionadas, normaliza grupos y añade sus etiquetas si faltan en el texto. Listas vacías, referencias inexistentes o inconsistentes se rechazan. El formato válido no demuestra soporte semántico; la evaluación también requiere leer las fuentes. El umbral inicial no es una frontera universal calibrada.

La UI envía hasta seis turnos completos del mismo filtro para reformular seguimientos. Las respuestas anteriores sirven para entender referencias, nunca como fuentes factuales. La respuesta usa evidencia recuperada de nuevo. La reformulación aparece en **Pregunta interpretada con el contexto** y añade una llamada a Google. El historial vive en la sesión y **Limpiar conversación** lo elimina. API: `history` alterna roles user/assistant en pares completos, hasta doce mensajes de 4,000 caracteres; un formato inválido devuelve 422.

Las consultas sobre primer/último cuento, capítulo o sección priorizan fragmentos de índice sin alterar scores. Los totales físicos de páginas PDF se extraen del archivo, incluidas páginas vacías, y se citan como document_metadata con score nulo. Contar todos los elementos requiere cobertura exhaustiva; top-k y contexto no garantizan ese conteo.

## Eliminar y reindexar

En **Biblioteca -> Eliminar un archivo indexado**, selecciona el origen y confirma. Se retiran solo sus chunks, embeddings y metadatos; el original permanece. La UI actualiza contadores/filtros, reinicia el contexto y conserva mensajes visibles. No se llama a Google. Un origen inexistente devuelve 404; uno vacío, 422. Puedes volver a ingerirlo. Las pruebas cubren eliminación selectiva persistente, originales intactos y reingestión en índices temporales.

## Validación y entrega

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q

# API activa y clave válida; consume cuota de Google.
.\.venv\Scripts\python.exe scripts/evaluate.py --ingest

# Regenerar el paquete limpio:
.\.venv\Scripts\python.exe scripts/package_delivery.py
```

El evaluador ejecuta tres preguntas del dominio y dos imposibles; conserva cada resultado y registra errores/reintentos temporales. `passed` revisa abstención y presencia de citas, no su significado. La revisión manual está en `evidence/VALIDATION.md`. Si la cuota impide un caso, queda como fallo pendiente en el registro; no se inventa una respuesta.

Las capturas de Streamlit y OpenAPI están descritas en `evidence/README.md`. Se incluye el informe final de una página en `output/pdf/reporte-aula-rag.pdf`. El paquete contiene código, corpus, configuración de ejemplo, pruebas, documentación y evidencias del corpus CC0; excluye `.env`, `.venv`, `chroma`, logs, cachés y documentos/capturas del PDF personal usado en pruebas previas.

## Referencias

- [Google AI: embeddings](https://ai.google.dev/gemini-api/docs/embeddings)
- [Google AI: salida estructurada](https://ai.google.dev/gemini-api/docs/structured-output)
- [Google AI: configuración del modelo](https://ai.google.dev/gemini-api/docs/latest-model)
- [Chroma: colecciones](https://docs.trychroma.com/docs/collections/configure)

