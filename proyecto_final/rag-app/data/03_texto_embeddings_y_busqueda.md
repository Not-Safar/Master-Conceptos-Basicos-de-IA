# Texto, embeddings y búsqueda semántica

## Del archivo al texto

Un sistema documental necesita extraer texto antes de generar vectores. Los archivos TXT y Markdown guardados en UTF-8 permiten una lectura directa. Un PDF puede contener texto seleccionable, imágenes de páginas o una combinación de ambos. Si sus páginas son solo imágenes, un extractor de texto puede devolver cadenas vacías. En ese caso se requiere reconocimiento óptico de caracteres, conocido como OCR, y una revisión de su calidad. Contar un PDF vacío como documento indexado produciría una falsa impresión de cobertura.

La extracción puede alterar el orden de lectura en columnas, perder tablas o unir encabezados con párrafos. Conviene inspeccionar algunos fragmentos y conservar el número de página para localizar el original. En documentos con cifras, una pérdida de formato puede cambiar la interpretación. Una tabla transformada en palabras sucesivas puede ocultar qué valor corresponde a qué encabezado. La recuperación semántica no corrige esos errores de entrada; solo busca relaciones entre las representaciones que recibió.

## Qué representa un embedding

Un embedding es una representación numérica de un elemento, como una palabra, una oración o un fragmento. Los modelos de embeddings convierten texto en vectores que permiten comparar relaciones de significado aproximadas. Dos expresiones con vocabulario diferente pueden quedar cercanas si se refieren al mismo tema. Esta cercanía resulta útil para encontrar un párrafo relevante cuando la pregunta no repite exactamente sus palabras. No debe interpretarse como una prueba de equivalencia lógica o de exactitud factual.

El espacio vectorial depende del modelo que produce las representaciones. Vectores de modelos diferentes no deben mezclarse en la misma búsqueda aunque tengan igual número de dimensiones. Las coordenadas pueden representar relaciones incompatibles. Si se cambia el modelo o una configuración que altera el espacio, se deben recalcular los vectores de todos los documentos y de las preguntas. Registrar el nombre del modelo y la dimensionalidad en la colección permite detectar una configuración incompatible antes de consultar.

## Similitud coseno

La similitud coseno compara la dirección de dos vectores. Se calcula dividiendo su producto punto entre el producto de sus normas. Cuando ambos vectores están normalizados a longitud uno, el producto punto coincide con esa similitud. En términos matemáticos, el resultado está entre menos uno y uno. Una puntuación mayor indica direcciones más cercanas, pero su distribución depende del modelo y del corpus. No existe un umbral universal que convierta automáticamente similitud en respuesta correcta.

Cuando un índice reporta distancia coseno definida como uno menos la similitud, la aplicación puede mostrar un score calculado como uno menos esa distancia. El score facilita comparar los fragmentos recuperados. No es una probabilidad de verdad ni un porcentaje de confianza. Un fragmento puede ser muy parecido a la pregunta y carecer del dato solicitado. Por ejemplo, un texto sobre seguridad de redes puede parecer relevante para una contraseña específica sin contenerla. El generador debe comprobar si existe evidencia suficiente.

## Partición en fragmentos

Dividir documentos en chunks permite recuperar partes específicas en lugar de enviar un archivo completo al modelo. Fragmentos demasiado pequeños pueden perder contexto: una definición puede separarse de su ejemplo o de una condición importante. Fragmentos demasiado grandes pueden incluir temas ajenos y gastar espacio de contexto. Elegir un tamaño implica equilibrar localización, coherencia y costo. Este proyecto usa ventanas de 300 palabras con 60 palabras de solapamiento como punto inicial para apuntes educativos.

El solapamiento repite las últimas palabras de una ventana al inicio de la siguiente. Reduce la posibilidad de que una explicación situada en un límite quede fragmentada sin contexto en ninguna ventana. No elimina todos los problemas de partición. También aumenta el número de vectores y puede producir resultados redundantes. En esta implementación se preserva la página del PDF y el índice del chunk; las ventanas no cruzan páginas. Para tablas o textos estructurados podría convenir una estrategia que respete secciones.

## Recuperación top-k

Una búsqueda top-k devuelve los k fragmentos más cercanos al vector de la pregunta. Recuperar más fragmentos aumenta la posibilidad de incluir evidencia útil, pero también puede introducir ruido y elevar el costo de generación. Un valor inicial de cuatro resulta manejable para una biblioteca pequeña, y la interfaz permite ajustarlo. Un filtro por archivo restringe la consulta cuando la persona desea trabajar con una fuente específica. El filtro debe aplicarse en el índice y no después de generar la respuesta.

La inspección de resultados permite separar dos problemas. Si el fragmento necesario no aparece, la recuperación necesita mejoras de extracción, partición, consulta o selección. Si aparece y el modelo responde mal, el problema está en el uso de evidencia o en la generación. Conservar texto, archivo, página y score en la respuesta de la API ayuda a diagnosticar esas diferencias sin depender únicamente de la impresión que produce el texto final.
