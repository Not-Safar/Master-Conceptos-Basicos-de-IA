# Reporte — Separación de blobs y elección de k

Se ejecutó en Google Colab el tutorial original de K-medias y se repitió el experimento separando los cinco centros generadores. Se conservaron 2000 puntos, `random_state=7` en `make_blobs` y los mismos hiperparámetros de KMeans en ambas corridas: inicialización `k-means++`, `n_init='auto'` y `random_state=42`. El primer ajuste mantuvo **k=5** y el barrido evaluó **k=1…9**, con silueta para **k=2…9**. Se utilizó scikit-learn 1.6.1.

Los nuevos centros fueron **(-4.0, 2.0), (-2.2, -3.5), (2.5, -3.0), (4.0, 1.4) y (0.0, 4.4)**. Las desviaciones estándar permanecieron en **[0.4, 0.3, 0.1, 0.1, 0.1]**, respectivamente. En el scatter modificado se distinguen cinco nubes separadas; el croquis adjunto muestra los centros y círculos de radio igual a su desviación estándar.

| Medida | Datos originales | Blobs separados |
|---|---:|---:|
| Inercia, k=3 | 653.2167 | 9644.1162 |
| Inercia, k=5 | 224.0743 | 216.3889 |
| Inercia, k=8 | 127.1314 | 135.3866 |
| k elegido visualmente por el codo | 4 | 5 |
| k con máxima silueta | 4 | 5 |
| Silueta máxima | 0.6885 | 0.9249 |

Las inercias de la tabla corresponden al barrido con los mismos parámetros, no al ejemplo adicional de inicialización `good_init` del tutorial.

En los datos de Géron, algunas nubes están próximas entre sí, especialmente las dos inferiores de la izquierda. Unir grupos cercanos permite una solución de cuatro clusters con un incremento relativamente pequeño de inercia. Por eso, aunque `make_blobs` utiliza cinco centros, el codo puede favorecer **k=4**: KMeans no conoce los grupos generadores. En esta corrida, la inercia bajó de **653.22 a 261.80** al pasar de k=3 a k=4, pero solo a **224.07** al añadir el quinto cluster. La silueta también alcanzó su máximo en k=4.

Con los centros separados, **ambos criterios coincidieron en k=5**. La inercia disminuyó de **4641.43 a 216.39** entre k=4 y k=5; después, en k=6, solo bajó a **179.48**. Ese cambio de pendiente respalda el codo en cinco. La silueta máxima fue **0.9249**, consistente con grupos bien separados. Las inercias se interpretan dentro de cada curva, porque mover los centros cambia la dispersión total de los datos.

Si el codo hubiera permanecido en cuatro, habría que revisar la distancia entre los centros más cercanos respecto a sus desviaciones y aumentar esa distancia o reducir la dispersión. En este experimento no fue necesario: separar los centros bastó para que ambos criterios señalaran cinco grupos.

**Evidencias:** notebook ejecutada con ambas corridas, cuatro pares de gráficas —scatter, Voronoi con k=5, codo y silueta—, croquis de centros, métricas exportadas y captura de la interfaz de Colab con los resultados del entorno.
