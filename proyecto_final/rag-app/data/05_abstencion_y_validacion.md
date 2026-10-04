# Abstención, citas y validación de RAG

## Qué significa responder con evidencia

Una respuesta con evidencia contiene afirmaciones sustentadas por fragmentos que una persona puede inspeccionar. Las citas deben apuntar a esos fragmentos reales y usar una numeración coherente. La existencia de una etiqueta como [1] no prueba que la frase anterior esté respaldada: se necesita leer la fuente. Evaluar un sistema RAG implica revisar la relación entre pregunta, evidencia y respuesta. Una explicación clara que introduce un dato ausente incumple el alcance documental, aunque el dato parezca plausible o sea verdadero en otro contexto.

La completitud también importa. Si una pregunta solicita dos condiciones y el corpus solo describe una, responder ambas con una suposición no es adecuado. Este proyecto adopta una regla conservadora: si la evidencia no cubre la pregunta completa, el modelo debe abstenerse. Una futura interfaz podría ofrecer respuestas parciales claramente delimitadas, pero necesitaría explicitar qué parte sí cuenta con soporte. En la versión educativa se prioriza una decisión sencilla y verificable.

## Dos criterios de abstención

El primer criterio es un umbral de similitud. Después de recuperar los vecinos, la API conserva solo los chunks cuyo score alcanza MIN_SCORE. Si ninguno lo supera, devuelve “No tengo evidencia suficiente en los documentos para responder esta pregunta” sin llamar al generador. El umbral inicial de este proyecto es 0.35 y necesita calibración con consultas reales. No está validado como una frontera universal entre preguntas válidas e inválidas. Su función es descartar contextos poco relacionados antes de generar.

El segundo criterio corresponde a Gemini. Aunque existan vecinos con un score alto, el prompt exige decidir si contienen la información necesaria. El modelo devuelve una salida estructurada con answer, abstained y citation_indices. Cuando decide abstenerse, la aplicación presenta un mensaje fijo de falta de evidencia y puede mostrar los fragmentos recuperados solo para inspección. Este criterio atiende preguntas que comparten vocabulario con el corpus pero solicitan un dato específico que no está documentado.

## Validación de citas

La API comprueba que una respuesta afirmativa contenga referencias numéricas, que esos números pertenezcan a los fragmentos entregados y que coincidan con la lista estructurada de citas del modelo. Si la salida está mal formada, carece de citas o usa referencias inexistentes, la aplicación se abstiene. Esta validación detecta problemas de formato y referencias inventadas. No demuestra automáticamente que cada afirmación esté respaldada ni elimina todas las posibles alucinaciones; revisar el significado de las fuentes sigue siendo necesario.

Los documentos y la pregunta se consideran datos, no instrucciones para cambiar el comportamiento del asistente. Un fragmento podría contener texto que ordena ignorar las reglas o inventar una respuesta. El prompt indica que esas instrucciones no se deben obedecer. Esta defensa reduce exposición, pero no ofrece una garantía absoluta contra inyección de instrucciones. Las pruebas deben incluir documentos o preguntas adversarias si el sistema se amplía a contenido de origen desconocido.

## Evaluar recuperación y generación

La recuperación se evalúa observando si los fragmentos necesarios aparecen entre los resultados top-k. Para hacerlo, se construyen preguntas con fuentes esperadas y se revisa la cobertura. Puede medirse la proporción de preguntas que recuperan al menos una fuente relevante, además de inspeccionar qué evidencia falta. Si la recuperación falla, ajustar el prompt del generador no resuelve la ausencia del contenido. Conviene revisar extracción, tamaño de chunks, solapamiento y elección de k.

La generación se evalúa por exactitud, soporte y cumplimiento del alcance. Una revisión manual puede marcar cada afirmación y asociarla con la cita que la respalda. También verifica que la respuesta esté en español y cubra la pregunta sin incorporar conocimiento externo. Separar errores de recuperación y generación ayuda a decidir cambios concretos. Aumentar k puede ayudar si faltan fuentes, mientras que exigir citas más claras puede ayudar cuando las fuentes ya están pero se utilizan de manera confusa.

## Casos positivos y negativos

Este corpus permite preguntar por diferencias entre aprendizaje supervisado y no supervisado, por el motivo del solapamiento y por la responsabilidad de ChromaDB. Son casos positivos porque hay explicaciones explícitas en los documentos. La contraseña del WiFi del salón 302 y la fecha de nacimiento de la profesora son casos negativos: el corpus no proporciona esos valores. Mencionar estas preguntas como ejemplos no aporta la información necesaria para responderlas. El comportamiento correcto es abstenerse, incluso si el fragmento que las menciona alcanza una similitud alta.

También se prueban un índice vacío, una pregunta en blanco, un archivo incompatible y un PDF sin texto. Reiniciar la API y consultar el mismo índice verifica persistencia. Repetir una ingestión sin cambios verifica que no aparezcan duplicados y que no se vuelvan a solicitar embeddings. Las pruebas automáticas con un proveedor simulado comprueban flujo y validación; las pruebas reales con Google son indispensables para evaluar calidad semántica, cuotas y compatibilidad de los modelos seleccionados.
