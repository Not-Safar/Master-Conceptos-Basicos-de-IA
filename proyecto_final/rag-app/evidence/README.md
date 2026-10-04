# Evidencias de entrega - corpus de IA

Estas pruebas usan el corpus original CC0 de data/. Los registros completos no son respuestas simuladas.

1. corpus-streamlit-answer.jpg: pregunta sobre solapamiento, respuesta en español con cita [1], fuente, score 0.688 y texto del chunk abierto. La barra lateral muestra cinco documentos y 18 chunks.
2. corpus-api-answer.jpg: la misma pregunta por POST /query en OpenAPI, cuerpo de petición y respuesta HTTP 200 con citas. evaluation.json incluye además la petición equivalente por httpx y sus fuentes completas.
3. corpus-streamlit-abstention.jpg: pregunta sobre la contraseña del WiFi del salón 302 y abstención explícita en Streamlit.
4. persistence-check.json: cinco documentos y 18 chunks antes y después de reiniciar FastAPI; PID nuevo, Streamlit activo y respuesta con fuentes tras el reinicio. Los tres registros separados se incluyen para inspección.
5. evaluation.json: tres consultas del dominio y dos negativas; cada caso registra decisión, citas o error HTTP y duración. Un error de cuota es un fallo del proveedor, no una abstención.
6. VALIDATION.md: lectura manual del soporte de las citas, incidentes de ejecución y límites.
7. delivery-check.json: comprobaciones finales del corpus, servicios y artefactos.

El informe de una página está en output/pdf/reporte-aula-rag.pdf. El ZIP contiene únicamente estas evidencias revisadas; las pruebas históricas con el PDF personal permanecen locales y no forman parte del paquete.

Para repetir la evaluación, inicia la API con tu propia clave y ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py --ingest
```

El índice no se incluye en la entrega. Biblioteca permite generarlo desde los cinco archivos compartidos. Las capturas y registros documentan la ejecución realizada; tu consulta puede redactarse de forma distinta o demorarse según el proveedor.
