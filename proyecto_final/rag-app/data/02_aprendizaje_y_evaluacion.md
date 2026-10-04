# Aprendizaje automático y evaluación

## Aprendizaje supervisado

El aprendizaje supervisado utiliza ejemplos que incluyen una entrada y una salida esperada, llamada etiqueta u objetivo. En clasificación, la salida es una categoría: un mensaje puede etiquetarse como correo deseado o correo no deseado. En regresión, la salida es una cantidad continua: por ejemplo, el tiempo estimado para completar un proceso. Durante el entrenamiento, un algoritmo ajusta parámetros para reducir una función de pérdida que compara la predicción con la salida esperada. La elección de esa función depende de la tarea y no determina por sí sola si el modelo será útil en una situación real.

Contar con etiquetas no significa que sean perfectas. Algunas pueden ser ambiguas, incorrectas o inconsistentes entre personas. Un proyecto debe explicar cómo se produjeron y qué representan. Si una etiqueta refleja una decisión histórica injusta, un modelo podría aprender a reproducirla. La evaluación necesita revisar tanto la exactitud general como los grupos o situaciones en que los errores se concentran. Documentar la procedencia y los criterios de etiquetado permite interpretar mejor los resultados.

## Aprendizaje no supervisado

El aprendizaje no supervisado trabaja con observaciones sin una salida objetivo para cada ejemplo. Busca estructura, como grupos de elementos similares o representaciones compactas. Un algoritmo de agrupamiento puede reunir documentos por temas sin recibir una lista de categorías correctas. El resultado requiere interpretación: un grupo matemático no necesariamente corresponde a una categoría útil para personas. También puede revelar diferencias de formato o longitud que no eran el foco del análisis.

La diferencia central entre aprendizaje supervisado y no supervisado es la presencia de una salida objetivo explícita en los ejemplos de entrenamiento. En el primero se aprende una relación entre entradas y etiquetas; en el segundo se exploran regularidades de los datos sin esas etiquetas. Ninguno es universalmente mejor. La elección depende de si hay objetivos definidos, datos etiquetados confiables y una forma apropiada de evaluar el resultado. Una misma aplicación puede combinar representaciones obtenidas sin etiquetas con un clasificador supervisado.

## Separación de datos

Para estimar cómo funciona un modelo con ejemplos nuevos, se separan conjuntos de entrenamiento, validación y prueba. El entrenamiento sirve para ajustar parámetros. La validación ayuda a seleccionar configuraciones. La prueba se reserva para una evaluación final después de tomar esas decisiones. No hay una proporción que sea adecuada para todos los problemas. Importan el volumen disponible, la independencia de los ejemplos y el tipo de cambio que se espera al usar el modelo.

La fuga de información ocurre cuando datos que deberían estar reservados influyen en el entrenamiento o en la selección del modelo. Puede suceder si registros duplicados aparecen en entrenamiento y prueba, o si una transformación calcula estadísticas usando todos los datos antes de dividirlos. En series temporales, usar observaciones futuras para construir variables del pasado puede inflar el desempeño. La separación debe representar la situación de uso y respetar relaciones entre personas, documentos o periodos.

## Sobreajuste y generalización

Un modelo sobreajusta cuando aprende particularidades del conjunto de entrenamiento que no se mantienen en ejemplos nuevos. Puede obtener una pérdida muy baja en entrenamiento y cometer muchos errores fuera de él. La generalización describe la capacidad de funcionar con observaciones no utilizadas para ajustar parámetros. Reducir complejidad, incorporar regularización y ampliar datos representativos son estrategias posibles, pero su utilidad debe comprobarse con una evaluación adecuada.

Un cambio en la distribución de datos también afecta el desempeño. Una aplicación entrenada con mensajes de un contexto puede encontrar vocabulario y hábitos distintos en otro. Por eso los resultados de una prueba no son una garantía permanente. Conviene observar errores durante el uso, revisar fuentes de cambio y reevaluar con casos actuales del alcance previsto. Esta observación debe evitar recoger información personal innecesaria y no sustituye la evaluación inicial.

## Métricas y lectura de resultados

En clasificación, la exactitud es la proporción de predicciones correctas. Puede ser engañosa cuando una clase es mucho más frecuente que otra. La precisión relaciona los verdaderos positivos con todos los casos predichos como positivos. La exhaustividad relaciona los verdaderos positivos con todos los positivos reales. La medida F1 combina precisión y exhaustividad mediante su media armónica. Una matriz de confusión muestra qué clases se confunden y permite interpretar errores específicos.

En regresión, el error absoluto medio resume diferencias absolutas entre predicciones y valores observados. El error cuadrático medio da mayor peso a diferencias grandes. La métrica debe relacionarse con el objetivo operativo. Además de un número agregado, conviene revisar ejemplos, segmentos y situaciones límite. Una herramienta RAG necesita métricas adicionales sobre recuperación, soporte de citas y abstención; evaluar solo la redacción final puede ocultar que los fragmentos relevantes nunca llegaron al generador.
