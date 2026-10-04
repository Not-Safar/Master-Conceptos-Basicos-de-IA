# Aula RAG

Aula RAG es una aplicación para hacer preguntas sobre una colección de documentos y obtener respuestas en español con citas a sus fuentes. Permite cargar archivos, incorporarlos al índice de búsqueda y revisar los fragmentos que respaldan cada respuesta. Cuando los documentos no contienen la información necesaria, indica que no puede responder.

La interfaz usa Streamlit y se comunica por HTTP con FastAPI. La API utiliza Google AI para convertir los textos en vectores y generar las respuestas, y ChromaDB para guardar y buscar los fragmentos. Esta guía explica cómo instalar la aplicación, usarla y modificar su funcionamiento.

## Requisitos

- Python 3.12. La aplicación se probó en Windows con Python 3.12.14.
- Una clave de [Google AI Studio](https://aistudio.google.com/apikey), con acceso a los modelos configurados y cuota disponible.
- Conexión a internet para instalar las dependencias y consultar Google AI.

Ejecuta los comandos desde la carpeta `rag-app`, donde se encuentran este README y `requirements.txt`. Los scripts `.ps1` están preparados para Windows; también puedes iniciar los servicios con los comandos de Python que se muestran más adelante.

## Instalación

En Windows, abre PowerShell y crea el entorno de Python:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Si `py` no está disponible, usa `python -m venv .venv` con Python 3.12 instalado. No necesitas activar el entorno cuando utilizas directamente su ejecutable.

En macOS o Linux, los comandos equivalentes son:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

`requirements.txt` contiene las versiones directas usadas por la aplicación. `requirements-lock.txt` conserva también las versiones de las dependencias del entorno probado en Windows; puedes instalar ese archivo si necesitas reproducir dicho entorno.

Abre `.env` con un editor de texto y completa esta variable con tu clave:

```dotenv
GOOGLE_API_KEY=tu_clave
```

Las demás opciones pueden conservar los valores de `.env.example`. Mantén `.env` fuera del control de versiones; `.gitignore` ya lo excluye. Si prefieres configurar la clave desde PowerShell, puedes definirla antes de iniciar la API:

```powershell
$env:GOOGLE_API_KEY = 'tu_clave'
```

Las variables del proceso tienen prioridad sobre `.env`. Reinicia la API después de cambiar su configuración.

## Iniciar y detener la aplicación

En Windows puedes iniciar ambos servicios en segundo plano:

```powershell
.\start-app.ps1
```

El script comprueba si ya están disponibles y guarda sus registros en `logs/`. Para reiniciar los servicios que inició este script, utiliza:

```powershell
.\restart-app.ps1
```

El reinicio verifica los procesos registrados antes de detenerlos. Si prefieres trabajar con terminales abiertas, inicia FastAPI en una terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal, inicia Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

También puedes usar `start-api.ps1` y `start-ui.ps1`, uno en cada terminal. Detén los servicios iniciados en primer plano con `Ctrl+C` en sus respectivas terminales. En macOS o Linux, sustituye `.\.venv\Scripts\python.exe` por `.venv/bin/python` y ejecuta los comandos manuales.

Abre la [aplicación](http://127.0.0.1:8501/) en el navegador. La [documentación de la API](http://127.0.0.1:8000/docs) permite consultar los endpoints y probar peticiones. Los servicios deben iniciarse nuevamente después de reiniciar el equipo.

## Usar la biblioteca y hacer preguntas

### Empezar con los documentos de ejemplo

1. Entra en **Biblioteca** y pulsa **Indexar los cinco documentos de ejemplo**.
2. Espera a que termine el proceso. Con la configuración incluida, los cinco textos producen 18 fragmentos.
3. En **Consultar**, escribe: **¿Por qué se utiliza solapamiento al dividir los documentos?**
4. Abre las fuentes debajo de la respuesta para revisar el texto, el archivo de origen, la posición y la similitud.

Los documentos de `data/` tratan sobre inteligencia artificial y RAG. Son cinco textos originales con 3,926 palabras, compartidos bajo licencia CC0; consulta `CORPUS_LICENSE.md`. Puedes probar una pregunta sin respuesta en ellos, como **¿Cuál es la contraseña del WiFi del salón 302?**. El sistema debe indicar que no tiene información suficiente.

El índice se crea al procesar documentos por primera vez y se guarda en `chroma/`. Reiniciar la API conserva los datos indexados.

### Incorporar tus archivos

En **Biblioteca**, selecciona uno o varios archivos PDF, Markdown o TXT y pulsa **Indexar archivos**. Los textos deben estar en UTF-8 y los PDF deben contener texto que pueda extraerse. Se admiten hasta 50 documentos por petición y un máximo de 10 MiB por archivo.

También puedes colocar archivos o subcarpetas dentro de `data/` y usar el campo de carpeta de la biblioteca. Las rutas se interpretan desde `data/`; una ruta `.` incluye sus documentos de forma recursiva. La API no permite usar este campo para leer rutas fuera de esa carpeta.

Cada archivo se identifica por su origen: `data/ruta.ext` para archivos de carpeta y `uploads/nombre.ext` para cargas desde el navegador. Los archivos cargados por la interfaz se procesan sin guardar una copia del PDF o archivo original en una carpeta del servidor; el índice conserva sus textos y vectores. Guarda tus originales si necesitas volver a cargarlos.

Si indexas otra vez el mismo contenido con el mismo origen, no se duplican los fragmentos ni se vuelven a solicitar sus embeddings. Si cambia el contenido, se actualizan los fragmentos de ese origen. Dos cargas con el mismo nombre representan el mismo archivo dentro del índice.

### Revisar respuestas y continuar una conversación

**Buscar en** permite consultar todos los documentos o elegir un archivo. **Fragmentos a recuperar** ajusta la cantidad de resultados que se envían al modelo. Las etiquetas `[1]`, `[2]` y siguientes corresponden a las fuentes visibles debajo de la respuesta.

La similitud se calcula como `1 - distancia coseno`. Indica cercanía entre el vector de la pregunta y el del fragmento; no expresa la probabilidad de que la respuesta sea correcta. Revisa el texto citado cuando necesites comprobar una afirmación.

La aplicación usa hasta seis turnos completos del mismo filtro para entender preguntas de seguimiento. Por ejemplo, puede interpretar a qué archivo se refiere una pregunta como «¿y cuántas páginas tiene?». La pregunta reformulada aparece en **Pregunta interpretada con el contexto**. Este paso añade una llamada a Google. Las respuestas anteriores ayudan a entender la pregunta, pero la respuesta nueva se basa en fuentes recuperadas de nuevo.

El historial se conserva en la sesión de Streamlit. **Limpiar conversación** elimina los mensajes y el contexto. Cada filtro mantiene su propio contexto durante la sesión.

### Retirar un archivo del índice

En **Biblioteca -> Eliminar un archivo indexado**, selecciona el origen, marca la confirmación y pulsa **Eliminar del índice**. Se eliminan sus fragmentos, vectores y datos de origen; los demás documentos y tus archivos originales se conservan. Esta operación no llama a Google.

La interfaz actualiza los contadores y filtros, y reinicia el contexto para las preguntas siguientes. Los mensajes anteriores permanecen visibles. Puedes incorporar nuevamente el archivo mediante una nueva carga o indexación de carpeta.

## Configuración

FastAPI lee su configuración al iniciar. Streamlit lee `API_BASE_URL` al ejecutar la interfaz; reinicia los servicios después de cambiar `.env`. Los valores de esta tabla corresponden a `.env.example`:

| Variable | Valor inicial | Función |
|---|---|---|
| `GOOGLE_API_KEY` | Vacío | Clave de acceso a Google AI |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Modelo que convierte textos y preguntas en vectores |
| `EMBEDDING_DIMENSIONS` | `768` | Dimensiones de los vectores |
| `GENERATION_MODEL` | `gemini-3.8-flash` | Modelo que redacta las respuestas |
| `GENERATION_THINKING_LEVEL` | `low` | Nivel de razonamiento para Gemini 3.8: `low`, `medium` o `high` |
| `CHUNK_SIZE` | `300` | Palabras por fragmento, entre 50 y 600 |
| `CHUNK_OVERLAP` | `60` | Palabras repetidas entre fragmentos; debe ser menor que el tamaño |
| `TOP_K` | `4` | Cantidad por defecto para consultas API que no envían `top_k` |
| `MIN_SCORE` | `0.35` | Similitud mínima para usar un fragmento como evidencia |
| `EMBEDDING_BATCH_SIZE` | `8` | Textos enviados por lote para calcular embeddings |
| `CHROMA_PATH` | `chroma` | Carpeta del índice persistente |
| `COLLECTION_NAME` | `curso_ia` | Nombre de la colección en Chroma |
| `API_BASE_URL` | `http://127.0.0.1:8000` | Dirección que usa Streamlit para llamar a la API |

La interfaz comienza con cuatro fragmentos y usa el valor de su control deslizante en cada consulta. `TOP_K` establece el valor por defecto de la API, no cambia ese control.

Puedes cambiar el modelo de generación sin volver a indexar. Comprueba que tu proyecto de Google tenga acceso al modelo elegido. Si no se define `GENERATION_MODEL`, el código usa `gemini-3.5-flash-lite`. Para Gemini 3.8, la configuración del cliente usa el nivel de razonamiento y omite los parámetros de muestreo `temperature`, `top_p` y `top_k`.

Cambiar el modelo o las dimensiones de los embeddings, o el tamaño y solapamiento de los fragmentos, requiere crear una colección distinta e indexar los documentos con la nueva configuración. Por ejemplo, asigna otro `COLLECTION_NAME`, reinicia la API e indexa los archivos. La colección anterior permanece guardada. El cliente actual admite `gemini-embedding-001`; usar otra familia de embeddings también requiere adaptar el código.

## Consultar la API desde otro programa

| Endpoint | Entrada | Respuesta |
|---|---|---|
| `GET /health` | Sin cuerpo | Estado del índice, modelos, documentos y total de fragmentos |
| `POST /ingest` | Formulario multipart con `files` y/o `paths` | Documentos y fragmentos nuevos, documentos omitidos y total |
| `POST /query` | JSON con `question`; `top_k`, `source` e `history` opcionales | Respuesta, citas, decisión de abstención y pregunta reformulada |
| `DELETE /documents` | JSON con el `source` exacto | Origen y cantidad de fragmentos eliminados |

`GET /health` informa si hay una clave configurada, pero no la muestra ni llama a Google para validarla. La documentación completa de campos y restricciones está en `/docs`.

Para consultar el estado y procesar `data/` desde PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
curl.exe -X POST http://127.0.0.1:8000/ingest -F 'paths=["."]'
```

`paths` es una lista JSON enviada como campo del formulario multipart. Para subir un archivo concreto:

```powershell
curl.exe -X POST http://127.0.0.1:8000/ingest -F 'files=@data/01_fundamentos_ia.md'
```

Puedes realizar una consulta desde Python con `httpx`, que ya forma parte de las dependencias:

```python
import httpx

with httpx.Client(base_url="http://127.0.0.1:8000", timeout=300) as client:
    response = client.post("/query", json={
        "question": "¿Por qué se utiliza solapamiento al dividir los documentos?",
        "top_k": 4,
    })
    response.raise_for_status()
    result = response.json()
    print(result["answer"])
    print("Abstención:", result["abstained"])
    for citation in result["citations"]:
        print(citation["index"], citation["source"], citation["score"])
```

Para limitar la consulta, añade `source` con un origen exacto obtenido de `/health`. Cada cita incluye `index`, `id`, `source`, `text`, `score`, `page`, `chunk_index` y `kind`. Los datos generales de un PDF, como su total de páginas físicas, se citan con `kind=document_metadata` y `score=null`, porque no representan un resultado de similitud vectorial.

Si tu cliente mantiene una conversación, puede enviar `history` como una lista alternada de mensajes `user` y `assistant`, cada uno con `role` y `content`. Se aceptan hasta seis pares completos y 4,000 caracteres por mensaje. La pregunta admite hasta 2,000 caracteres y `top_k` valores entre uno y diez.

## Modificar la aplicación

El flujo de una pregunta es: interpretar el contexto, calcular su vector, recuperar fragmentos, seleccionar evidencia y generar la respuesta. La indexación se realiza por separado: extraer texto, dividirlo, calcular vectores y guardarlos.

```text
Navegador -> Streamlit :8501 -> HTTP -> FastAPI :8000
                                      |-> Google AI: embeddings y generación
                                      |-> ChromaDB: almacenamiento y búsqueda
```

| Archivo | Responsabilidad |
|---|---|
| `app/main.py` | Endpoints, arranque de la API, CORS y manejo de errores |
| `app/config.py` | Variables de configuración y validaciones |
| `app/schemas.py` | Campos de entrada y salida de la API |
| `app/documents.py` | Lectura de archivos, formatos, límites y rutas |
| `app/chunk.py` | División del texto y solapamiento |
| `app/embed.py` | Cliente de Google AI, embeddings y errores del proveedor |
| `app/store.py` | Persistencia, búsqueda y actualización en Chroma |
| `app/service.py` | Coordinación de la indexación, consulta y eliminación |
| `app/retrieval.py` | Consultas de orden y metadatos de páginas PDF |
| `app/conversation.py` | Reformulación de preguntas con historial |
| `app/generate.py` | Instrucciones del modelo y validación de citas |
| `app/generation_config.py` | Opciones de generación según el modelo |
| `ui/streamlit_app.py` | Interfaz y llamadas HTTP a FastAPI |
| `.streamlit/config.toml` | Temas claro y oscuro |
| `tests/` | Pruebas de la API, índice e interfaz |

Para cambiar textos o controles, modifica `ui/streamlit_app.py`. Para ajustar la forma de responder, revisa las instrucciones de `app/generate.py` y comprueba tanto respuestas con evidencia como preguntas sin respuesta. Los cambios en extracción, fragmentación o embeddings requieren revisar cómo se actualizarán los documentos ya indexados.

Si añades un campo o endpoint, actualiza `app/schemas.py` y `app/main.py`, su uso en la interfaz y las pruebas correspondientes. La interfaz debe seguir accediendo al índice y a Google a través de la API. Chroma recibe los vectores calculados por Google; no utiliza su propio generador de embeddings.

Durante el desarrollo puedes iniciar Uvicorn con recarga automática en lugar de la API habitual:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Detén primero la API que ocupa el puerto 8000. Para el uso normal, mantén un solo proceso Uvicorn: las operaciones de indexación, consulta y eliminación se coordinan dentro de ese proceso.

## Comprobar los cambios

Instala las dependencias de desarrollo y ejecuta las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Las pruebas locales usan Chroma real y un proveedor de Google simulado, por lo que no necesitan una clave ni consumen cuota. Comprueban la división de textos, persistencia, actualización, eliminación, citas, contexto y estados de error.

Para evaluar consultas con Google real, inicia la API con una clave válida y ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py --ingest
```

Este comando procesa `data/` y realiza tres preguntas sobre los documentos y dos sin respuesta. Consume cuota y guarda los resultados en `evidence/evaluation.json`, con los errores e intentos registrados. El campo `passed` comprueba la decisión de abstención y la presencia de citas; lee también las respuestas y sus fuentes para revisar el contenido. `evidence/VALIDATION.md` muestra una revisión de referencia.

## Problemas habituales y límites

| Situación | Acción recomendada |
|---|---|
| El navegador muestra conexión rechazada | Inicia ambos servicios y verifica sus puertos |
| Streamlit informa que no conecta con FastAPI | Comprueba la API en `/health` y el valor de `API_BASE_URL` |
| Falta la clave o Google rechaza los permisos, HTTP 503 | Revisa `.env`, el acceso de la clave y reinicia la API |
| Google devuelve HTTP 429 | Espera y revisa la cuota antes de repetir la petición |
| La API devuelve HTTP 502 | Revisa conexión, modelo y registros; puede ser un fallo temporal de Google |
| La colección no coincide con la configuración | Usa otra colección e indexa con los parámetros actuales |
| El archivo se rechaza | Comprueba formato, codificación, texto disponible y tamaño máximo |
| La petición devuelve HTTP 422 | Revisa pregunta, campos e historial en `/docs` |
| Un archivo eliminado devuelve HTTP 404 | Actualiza la biblioteca y comprueba su origen |

Una pregunta sin evidencia devuelve HTTP 200 con `abstained=true`. Un error de Google no es una abstención: indica que la petición no pudo completarse. El umbral de 0.35 es un valor inicial y puede necesitar ajustes. Las citas válidas tampoco garantizan por sí solas que una afirmación esté respaldada.

La extracción de PDF no incluye reconocimiento de texto en imágenes (OCR). Las preguntas que requieren contar todos los elementos de un documento necesitan revisar su contenido completo; recuperar unos pocos fragmentos puede ser insuficiente. Si hay varios PDF, selecciona uno para preguntar por su total de páginas. Las consultas de primer o último cuento, capítulo o sección priorizan fragmentos de índice cuando están disponibles.

Las actualizaciones de varios documentos no forman una única transacción de disco. Una falla de Google antes de escribir conserva el índice anterior, pero una falla de almacenamiento durante la escritura puede dejar una actualización parcial. Conserva tus originales y haz una copia de `chroma/` con la API detenida si necesitas respaldar el índice.
