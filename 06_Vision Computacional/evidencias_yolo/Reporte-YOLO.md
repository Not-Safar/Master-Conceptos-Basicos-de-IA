# Reporte: detección de objetos con YOLOv8

Se ejecutó en Google Colab con GPU **Tesla T4** una copia del tutorial de Ultralytics. Se conservó el modelo **yolov8n.pt** y se completaron **3 épocas de entrenamiento sobre coco128.yaml**. Primero se guardaron las predicciones originales de `zidane.jpg` y `bus.jpg`; después se sustituyeron ambas fuentes por la misma imagen, `mi_foto.png`, que muestra personas utilizando teléfonos celulares. No se modificaron los umbrales de predicción.

| Imagen y vía de predicción | Clases detectadas y cantidades | Total de cajas |
|---|---|---:|
| Zidane, CLI | 2 `person` y 1 `tie` | 3 |
| Bus, Python | 4 `person`, 1 `bus` y 1 `stop sign` | 6 |
| Imagen seleccionada, CLI | 4 `person`, 1 `remote` y 2 `cell phone` | 7 |
| Imagen seleccionada, Python | 2 `person`, 2 `remote` y 2 `cell phone` | 6 |

**Objetos omitidos y errores.** En la imagen seleccionada, el teléfono desenfocado del primer plano no recibió una etiqueta de celular. El desenfoque y la oclusión parcial podrían dificultar su reconocimiento, aunque no se hicieron pruebas adicionales para confirmar la causa. Como `cell phone` sí pertenece a COCO, la omisión no se explica por ausencia de esa clase. Además, se observaron cajas de `remote` sobre teléfonos, lo que indica confusión de clases. En la salida de Python aparecen etiquetas de celular y control remoto sobre los mismos objetos; por ello, el total de cajas no equivale necesariamente al número de objetos distintos.

**Comparación CLI y Python.** Las predicciones coincidieron en las tres clases emitidas y en dos cajas de celular, pero difirieron en personas, controles remotos y confianzas. El CLI produjo siete cajas y Python seis. El CLI cargó los pesos preentrenados de `yolov8n.pt`, mientras que Python utilizó el modelo después del entrenamiento, con el checkpoint `best.pt`. Por tanto, no se puede atribuir la diferencia únicamente a usar una interfaz u otra ni afirmar que el entrenamiento mejoró esta imagen.

El ejercicio mostró detecciones útiles junto con omisiones y clasificaciones incorrectas. Se conservaron las cuatro imágenes con cajas, sus capturas en Colab, el notebook ejecutado y las evidencias de GPU y entrenamiento.
