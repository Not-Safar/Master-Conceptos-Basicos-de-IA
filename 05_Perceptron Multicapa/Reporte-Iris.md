# Reporte: más capas en el perceptrón multicapa con Iris

Se ejecutaron en Google Colab los notebooks de NumPy y Keras, comparando la arquitectura original **4–3–3** con la profunda **4–3–3–3–3**. Se conservaron la activación sigmoide, SGD con tasa de aprendizaje de **0.03** y **500 épocas**. La red profunda tiene tres capas ocultas y una de salida, todas de tres neuronas. Los resúmenes de Keras confirmaron dos y cuatro capas Dense, con 27 y 51 parámetros entrenables, respectivamente.

| Implementación y versión | MSE final | Aciertos en entrenamiento | Tiempo (s) |
|---|---:|---:|---:|
| NumPy original del curso | 0.02093 | 96.00 % | 9.07 |
| NumPy profunda corregida | 0.13547 | 70.67 % | 9.99 |
| Keras original | 0.15084 | 66.67 % | 34.85 |
| Keras profunda | 0.22171 | 50.00 % | 36.13 |
| NumPy control corregido, 4–3–3 | 0.01987 | 96.67 % | 5.87 |

**Efecto de añadir capas.** En ambas implementaciones, la red profunda terminó con mayor error y menor porcentaje de aciertos. En NumPy, las redes pequeñas redujeron progresivamente el error, mientras que la profunda permaneció casi estancada durante buena parte del entrenamiento y descendió con mayor rapidez cerca del final. En Keras, la red original continuó mejorando hasta la época 500; la profunda se estabilizó alrededor de un MSE de 0.222. Añadir capas aumentó el tiempo medido y no mejoró la clasificación en estas corridas.

**Comparación de implementaciones.** Las curvas con la misma topología no fueron iguales. NumPy actualiza los pesos después de cada muestra y mantiene el orden de Iris; Keras usa lotes de 32 y mezcla los datos. Esto representa aproximadamente 150 actualizaciones por época en NumPy y cinco en Keras. También difieren la inicialización, la escala de los gradientes y la evaluación de la pérdida. El error original de NumPy suma los errores cuadrados de las tres salidas y promedia entre muestras; Keras promedia también entre salidas. Por eso la tabla utiliza un MSE calculado con los pesos finales y la misma definición en ambos casos. Los errores finales propios del notebook de NumPy fueron 0.06279 y 0.40642; las últimas pérdidas registradas por Keras fueron 0.15091 y 0.22172.

Además, el código original de NumPy intercambia los índices de los pesos al propagar el error hacia la capa oculta y actualiza los pesos de salida antes de calcular todos los deltas. Se conservó esa corrida y se añadió un control pequeño con el mismo backprop corregido de la red profunda. Este control obtuvo un MSE de 0.01987, frente a 0.13547 de la profunda: el empeoramiento también aparece al comparar ambas profundidades con el algoritmo corregido. Los tiempos incluyen distintas tareas de evaluación y ejecución, por lo que no constituyen una comparación aislada de velocidad entre bibliotecas.

**Interpretación.** Al apilar sigmoides, la retropropagación multiplica derivadas que pueden reducir considerablemente los gradientes. Esto es compatible con el aprendizaje lento o estancado observado, aunque las gráficas no demuestran por sí solas que esa sea la única causa. Con MSE y este presupuesto de entrenamiento, una mayor profundidad no garantizó mejores resultados en Iris. Las conclusiones corresponden a estas ejecuciones con semilla fijada; los porcentajes reportados son de entrenamiento y no permiten afirmar cómo se comportarán las redes con datos nuevos.
