# Arquitectura de un sistema RAG

## Recuperar antes de generar

La generación aumentada por recuperación, llamada RAG, combina una búsqueda sobre fuentes disponibles con la producción de una respuesta. El orden importa: primero se obtienen fragmentos relacionados con la pregunta y después el modelo recibe esa evidencia. Enviar únicamente la pregunta a un modelo de lenguaje no constituye este flujo documental. La respuesta debe depender de lo recuperado y permitir que una persona localice las fuentes. Un sistema RAG puede reconocer que su biblioteca no contiene información suficiente para responder.

La indexación y la consulta son procesos distintos. Durante la indexación se extrae texto, se divide en fragmentos, se calculan embeddings de documentos y se almacenan vectores con metadatos. Durante una consulta se calcula el embedding de la pregunta, se buscan vecinos y se selecciona evidencia. Finalmente se genera la respuesta con referencias numeradas. La indexación suele repetirse cuando cambia el corpus; calcular el vector de la pregunta ocurre en cada consulta.

## Responsabilidad de Streamlit

Streamlit presenta la interfaz. Permite subir archivos, solicitar su indexación, escribir una pregunta y revisar respuestas y fuentes. También muestra estados vacíos y errores útiles: API sin conexión, falta de credenciales o biblioteca todavía vacía. Su responsabilidad es enviar peticiones HTTP y presentar resultados. En esta arquitectura no calcula embeddings, no llama directamente a Google AI y no abre la base ChromaDB. Esta separación permite que las reglas del sistema estén concentradas en un servicio.

El historial de preguntas en la sesión facilita revisar interacciones previas. Tener un historial visual no implica que cada pregunta use las anteriores como contexto. En este proyecto cada consulta es independiente, y el historial vive solo en la sesión de Streamlit. Una aplicación conversacional con referencias como “ese documento” necesitaría resolver explícitamente esos antecedentes antes de recuperar evidencia. Esa extensión requiere diseño adicional para conservar trazabilidad y evitar interpretar mal el alcance.

## Responsabilidad de FastAPI

FastAPI expone operaciones HTTP documentadas. El endpoint GET /health informa si la API está disponible, si Chroma es accesible y cuántos documentos y chunks hay. POST /ingest recibe archivos o rutas autorizadas, extrae su texto y ejecuta la indexación. POST /query recibe una pregunta y un top_k opcional, realiza recuperación y devuelve answer, citations y abstained. La documentación OpenAPI en /docs permite inspeccionar las entradas y probar peticiones sin usar la interfaz.

La API valida preguntas en blanco, formatos no admitidos y archivos sin texto. Un problema de clave o cuota debe producir un mensaje de servicio, mientras que una pregunta ajena al corpus debe devolver una abstención normal. No son la misma situación. Centralizar esos comportamientos permite que Streamlit y otro cliente HTTP reciban reglas consistentes. La API también limita las rutas locales a la carpeta data para evitar lecturas arbitrarias de archivos del servidor.

## Responsabilidad de Google AI

Google AI realiza dos tareas diferentes. El modelo de embeddings transforma fragmentos y preguntas en vectores comparables. El modelo generativo Gemini redacta una respuesta en español a partir de la evidencia recuperada. Los modelos de chat no sustituyen al modelo de embeddings. En este proyecto los documentos usan el tipo de tarea RETRIEVAL_DOCUMENT y las preguntas usan RETRIEVAL_QUERY con el mismo modelo de embeddings y la misma dimensionalidad.

La clave de acceso se configura en un archivo .env local y no se incluye en la entrega. Un archivo .env.example documenta las variables sin contener credenciales. Si la clave cambia, el servicio necesita recargar su configuración. Las llamadas pueden fallar por conexión, permisos o cuota; reintentos limitados ayudan con errores transitorios, pero no deben ocultar fallas persistentes. Procesar pequeños lotes de embeddings facilita controlar el trabajo y evita peticiones innecesariamente grandes.

## Responsabilidad de ChromaDB

ChromaDB almacena vectores, texto y metadatos y realiza búsqueda de vecinos. La API le proporciona los embeddings ya calculados por Google; no usa un generador de embeddings implícito de Chroma. La colección se guarda en una ruta de disco para conservarse después de reiniciar el proceso. Los metadatos incluyen source, página e índice del chunk. Mantener estas referencias permite presentar evidencia legible y rastrear el origen de una respuesta.

Reindexar un documento con el mismo origen debe actualizarlo sin duplicar indefinidamente sus fragmentos. Un fingerprint del contenido permite omitir documentos sin cambios. Para un documento cambiado se calculan los nuevos vectores, se guardan y se eliminan chunks obsoletos de ese origen. El almacenamiento local no reemplaza una estrategia de respaldo ni proporciona automáticamente transacciones para una operación de varios archivos. El proyecto educativo trabaja con un solo proceso de API y serializa ingestión y consulta para evitar lecturas intermedias dentro de él.
