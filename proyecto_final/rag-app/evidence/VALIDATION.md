# Revisión manual y aceptación - 2 de octubre de 2026

La evaluación usa Google AI real a través de FastAPI, con el corpus CC0 de cinco archivos y 18 chunks. Los resultados completos y tiempos por intento están en evaluation.json. Esta revisión corresponde a estas consultas concretas; no mide calidad general ni calibra un umbral universal.

| Pregunta | Revisión del soporte | Resultado |
|---|---|---|
| Diferencia entre supervisado y no supervisado | Las citas [1] y [2] de 02_aprendizaje_y_evaluacion.md describen explícitamente entrada/etiqueta frente a observaciones sin objetivo y exploración de estructura. No se introducen datos ajenos. | Respuesta en español con soporte |
| Motivo del solapamiento | La cita [1], chunk 3 de 03_texto_embeddings_y_busqueda.md, explica repetir las palabras finales y reducir la pérdida de contexto en límites. La similitud real es 0.688411. | Respuesta en español con soporte |
| Evaluar recuperación y citas | Las citas [3] y [4] de 05_abstencion_y_validacion.md describen cobertura top-k, proporción de fuentes relevantes, validación de referencias y revisión manual de afirmaciones. La cita [1] explica que una etiqueta por sí sola no demuestra respaldo. | Respuesta en español con soporte |
| Contraseña del WiFi del salón 302 | El corpus solo menciona esta pregunta como ejemplo imposible, sin proporcionar una contraseña. Hay vecinos sobre 0.35, pero Gemini se abstuvo. | Abstención, HTTP 200 |

| Fecha de nacimiento de la profesora | El corpus menciona la pregunta como ejemplo negativo, sin una fecha. Tras un error 429, el reintento devolvió abstención con HTTP 200; ambos intentos se conservan. | Abstención, HTTP 200 |

Resultado final: cinco de cinco casos aprobados (tres respuestas y dos abstenciones).

## Ejecución y errores

La primera ejecución se interrumpió con HTTP 502 en la segunda pregunta. Se modificó el evaluador para guardar resultados incrementalmente y registrar hasta tres intentos ante 502/503/504, sin tratar errores como abstención. En la evaluación siguiente pasaron las tres preguntas positivas y la del WiFi; la pregunta adicional sobre nacimiento de la profesora encontró HTTP 429. OpenAPI también encontró inicialmente un 429 y, al repetir después de esperar, devolvió HTTP 200 con la misma consulta sobre solapamiento. Tras esperar, se reintentó únicamente la consulta sobre nacimiento: HTTP 200 y abstención correcta en 1.94 segundos, conservando el intento 429 y su detalle en evaluation.json. Estos fallos del proveedor se declaran; no se sustituyeron por respuestas simuladas.

## Comprobaciones adicionales

- 68 pruebas locales aprobadas, con Chroma real y Google simulado solo en tests. Un aviso de deprecación de Starlette no afecta el resultado.
- Reingestión de data/ sin cambios: cinco documentos omitidos, cero chunks nuevos, total 18; no hubo duplicación.
- Reinicio real: la API cambió de PID, Streamlit permaneció activo y los documentos/chunks fueron idénticos antes/después. La consulta posterior respondió correctamente sin reingestión; registro en persistence-check.json.
- Capturas reales de respuesta con fuente, score y texto; misma pregunta por OpenAPI; abstención en Streamlit. No contienen la clave.
- Reporte generado con ReportLab, confirmado como una página mediante pypdf y revisado visualmente tras renderizar con Poppler.
- Paquete construido mediante lista explícita de archivos permitidos; comprobación de integridad ZIP y clave de ejemplo vacía. No incluye el PDF personal de las pruebas previas ni sus capturas.

## Límites

La aplicación requiere acceso y cuota de Google. La validación de citas no garantiza automáticamente el significado de todas las respuestas. PDF escaneados, conteos globales y transacciones de disco de varios documentos permanecen fuera del alcance cubierto. Docker Compose es opcional en la consigna y no se incluye.

