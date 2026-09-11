# Reporte — A* en el mapa de México

Se adaptó A* del ejercicio de Rumania para encontrar rutas de menor costo en el grafo de México. La implementación utiliza una cola de prioridad ordenada por `f(n) = g(n) + h(n)`, registra el mejor costo conocido y reconstruye el camino mediante los padres de los nodos. El costo de cada movimiento es `edges[].km` y cada arista se recorre en ambos sentidos.

**Estado y duplicados.** El estado es el ID entero de una ciudad. Así, dos ciudades llamadas Puebla o Guadalupe siguen siendo estados diferentes. El CLI rechaza nombres ambiguos y muestra las alternativas; permite indicar estado o `id:N`. En el mapa, las sugerencias muestran nombre, estado e ID. Nunca se selecciona un duplicado al azar.

**Heurística.** Se calcula haversine desde las coordenadas de cada ciudad hasta el destino. La distancia geográfica directa no supera la suma de distancias geográficas de un camino, por la desigualdad del triángulo. Hay un detalle en los datos: los kilómetros están redondeados a dos decimales, de modo que la haversine exacta puede exceder ligeramente una arista almacenada. Se multiplica por un factor conservador `alpha ≈ 0.998517792300`, calculado a partir del menor cociente entre costo almacenado y distancia geográfica de cada arista. Así `alpha·d(u,v) ≤ costo(u,v)` y `h(u) ≤ costo(u,v) + h(v)`; con `h(destino)=0`, la heurística es consistente y admisible sin alterar el grafo.

**Resultados.** Tijuana → Cancún costó **4,528.20 km**, con **125 saltos**, **126 ciudades** y **949 nodos expandidos**. UCS obtuvo el mismo costo y expandió 998 nodos. Mexico City → Monterrey costó **1,041.87 km**, con **27 saltos** y **428 expansiones**, frente a 783 con UCS. Se excluye la meta del conteo de expansiones.

Python y el navegador produjeron el mismo camino y métricas en las cuatro parejas sugeridas. Las capturas y salidas del CLI están en `evidencias/`. El mapa dibuja el recorrido completo. Se conservaron las 1,000 ciudades y 2,565 aristas originales y se verificó la identidad del JSON mediante SHA-256.
