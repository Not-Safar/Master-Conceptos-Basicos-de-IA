# Fundamentos de inteligencia artificial

## Propósito y alcance

La inteligencia artificial estudia sistemas capaces de realizar tareas que requieren interpretar información, aprender patrones, planear acciones o producir respuestas útiles. Una aplicación concreta suele combinar varios componentes: datos, reglas, modelos estadísticos y una interfaz. Llamar inteligente a una aplicación no implica que tenga conciencia ni que comprenda el mundo como una persona. Para evaluar un sistema conviene describir primero qué tarea resuelve y qué errores resultan relevantes. Clasificar mensajes, identificar defectos de fabricación y consultar una biblioteca son tareas diferentes y necesitan criterios diferentes.

En este corpus el objetivo de una herramienta de consulta es responder preguntas sobre documentos disponibles, mostrar la evidencia y reconocer cuándo esa evidencia falta. La herramienta no pretende resolver cualquier pregunta posible. Definir un alcance explícito permite distinguir un resultado correcto de una respuesta que suena convincente pero introduce información ajena. Una respuesta breve con referencias verificables puede ser más útil que una explicación extensa que mezcla varias fuentes sin identificarlas.

## Reglas, aprendizaje y generación

Un sistema basado en reglas aplica instrucciones escritas por personas. Por ejemplo, una regla puede marcar como incompleto un formulario que carece de un campo obligatorio. Sus decisiones son fáciles de inspeccionar cuando las reglas son simples, pero mantener miles de excepciones resulta difícil. Un modelo de aprendizaje automático ajusta parámetros a partir de ejemplos. Puede detectar regularidades que no se expresan fácilmente como reglas, aunque también puede aprender relaciones accidentales o sesgadas presentes en los datos.

Los modelos generativos producen contenido como texto, imágenes o audio. En el caso de texto, un modelo de lenguaje predice secuencias de unidades llamadas tokens. Su fluidez permite redactar explicaciones y sintetizar documentos, pero no garantiza veracidad. Puede producir una cifra o referencia inexistente porque esa secuencia encaja con patrones aprendidos. Esta posibilidad exige mecanismos de evaluación y un diseño que permita contrastar los resultados contra fuentes conocidas.

## Datos y representación

Los datos son observaciones registradas para un propósito. Pueden contener números, categorías, texto o imágenes. Antes de entrenar o consultar un modelo se necesita decidir cómo representarlos. Una variable numérica podría requerir normalización; una categoría podría transformarse en indicadores; un texto puede convertirse en un vector de características. Estas transformaciones afectan qué relaciones podrá reconocer el sistema. Una representación adecuada para comparar temas no necesariamente sirve para verificar si dos cifras son iguales.

La calidad de los datos incluye integridad, consistencia, cobertura y procedencia. Si una biblioteca mezcla versiones viejas y nuevas de un manual sin distinguirlas, una recuperación correcta en términos de similitud podría traer una instrucción obsoleta. Si solo hay documentos sobre un tema, el sistema no debe asumir que también dispone de información sobre temas vecinos. Conservar el nombre del archivo y la ubicación del fragmento ayuda a que la persona detecte esos límites.

## Tareas y criterios de éxito

Una tarea debe formularse de manera observable. En clasificación se pregunta si la categoría predicha coincide con una etiqueta. En regresión se mide la diferencia entre una cantidad estimada y una cantidad observada. En una consulta documental se verifican varios aspectos: si se recuperaron fragmentos relevantes, si la respuesta cubre la pregunta, si las citas existen y si realmente respaldan las afirmaciones. Estas comprobaciones no deben reducirse a una impresión general de calidad.

El criterio de éxito también depende del costo del error. Una sugerencia musical equivocada puede tener poco impacto; una instrucción técnica incorrecta puede provocar pérdida de trabajo. Un proyecto educativo debe hacer visible la incertidumbre y facilitar la inspección. Para consultas fuera del corpus, el comportamiento esperado es indicar falta de evidencia. Abstenerse correctamente forma parte del desempeño y no equivale a una falla de conexión o a un error de programación.

## Ejemplo de delimitación

Imagina una biblioteca con cinco apuntes sobre inteligencia artificial. La pregunta sobre la diferencia entre clasificación y regresión pertenece a su alcance si esos conceptos están descritos. La pregunta sobre una contraseña de red, el cumpleaños de una docente o un resultado deportivo no está respaldada por esos apuntes. Aunque el modelo pueda conocer hechos públicos relacionados, la aplicación de consulta debe limitarse al corpus recibido. Su promesa es responder con evidencia localizable, y esa promesa exige no rellenar huecos con conocimiento externo.

## Responsabilidad del diseño

Las decisiones de diseño determinan cómo se presentan fuentes, errores y límites. Una interfaz debe mostrar cuándo no hay documentos, cuándo la API está caída y cuándo la pregunta está vacía. También debe distinguir la falta de evidencia de la ausencia de una clave de acceso. Esas situaciones requieren acciones diferentes: cargar archivos, iniciar el servidor, escribir una pregunta o configurar credenciales. Hacerlas explícitas ayuda a usar y evaluar el sistema sin atribuir cualquier problema al modelo.
