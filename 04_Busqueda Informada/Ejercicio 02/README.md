# Ejercicio 2 — Rutas con A* en México

Calcula rutas de menor costo sobre el grafo original de 1,000 ciudades y 2,565 aristas. Incluye CLI en Python y mapa interactivo local. Los kilómetros corresponden a las conexiones del grafo; no son rutas por carretera.

## Ejecutar Python

Requiere Python 3.10 o posterior; no necesita instalar paquetes. Abre una terminal en esta carpeta y ejecuta:

```powershell
python find_route.py --from-city Tijuana --to Cancún
python find_route.py --from-city "Mexico City" --to Monterrey
```

Si Windows usa el lanzador `py`, sustituye `python` por `py`. Se imprime Status, From, To, Path completo, Depth (hops), Cost (km), Expanded y Heuristic. `Expanded` cuenta nodos extraídos de la frontera cuyos vecinos se examinan; excluye la meta y las entradas obsoletas.

Los nombres respetan acentos y espacios: `Mexico City`, `Cancún`, `Mérida`. Para nombres repetidos debes indicar estado o ID; el programa muestra las opciones y termina con error si falta desambiguar:

```powershell
python find_route.py --from-city Puebla --from-state Puebla --to Cancún
python find_route.py --from-city id:6 --to id:25
```

Opciones adicionales: `--json` imprime un resultado estructurado con IDs; `--ucs` usa h = 0 para comparar con búsqueda de costo uniforme; `--graph ARCHIVO` permite indicar otro JSON compatible. Códigos de salida: 0 éxito, 1 sin camino, 2 entrada inválida.

## Usar el mapa

1. Extrae el ZIP. El mapa es autónomo: puedes copiar y abrir únicamente `mexico_map.html`; lleva el grafo y todo el JavaScript integrado.
2. Abre `mexico_map.html` con Edge, Chrome o Firefox. Funciona sin servidor y sin conexión.
3. Escribe un nombre exacto en Origen y Destino, o elige una sugerencia con **nombre, estado e ID**.
4. Pulsa **Calcular ruta A***. Azul marca todas las conexiones y ciudades del camino; verde es el origen y naranja el destino. El panel muestra km, saltos, expansiones y heurística.
5. Abre **Ver recorrido completo** para consultar todas las ciudades. Los botones de ejemplo calculan las dos rutas de las capturas. **⇄** intercambia los extremos; **Limpiar** retira la ruta; **Centrar vista** ajusta el mapa.

La búsqueda de ciudades, filtro por estado, exploración de vecinos y zoom originales siguen disponibles. La ruta tiene su propia capa, por lo que los filtros no ocultan partes del camino. Un nombre ambiguo muestra un error con las opciones: selecciona una sugerencia para resolverlo.

## Código y reutilización

- `route_search.py`: Graph, Node, RouteFindingProblem, haversine y A*.
- `find_route.py`: argumentos y salida de terminal.
- `route_search.js`: puerto del mismo algoritmo con heap mínimo y desempate por inserción.
- `route_ui.js`: controles, validación, métricas y dibujo de la ruta.
- `sync_map.py`: integra ambos módulos JavaScript en el HTML. Ejecuta `python sync_map.py` si editas alguno de los módulos; no regenera el grafo.
- `mexico_map.html`: mapa original con los controles añadidos; conserva su grafo incrustado.
- `referencia/`: copias originales de `search/astar.py`, `romania/node.py` y `romania/problem.py` del proyecto **Búsqueda informada/project**. Solo son referencia; no se ejecutan.

La adaptación conserva la frontera por `f = g + h`, mejores costos conocidos y reconstrucción con padres. Los estados ahora son IDs enteros y las aristas son bidireccionales. La fórmula haversine procede de `Mexico map/generate_mexico_graph.py` (radio 6371 km).

**Precisión de la heurística:** el generador redondeó los pesos a dos decimales. Haversine sin ajustar puede superar ligeramente algunos de esos pesos. Por eso se usa `h(n) = alpha × haversine(n, destino)`, con `alpha = min(1, min_arista(km / haversine(extremos))) × (1 - 10⁻¹²)`, aproximadamente **0.998517792300**. Esto asegura consistencia y admisibilidad sobre los pesos almacenados, manteniendo intacto el JSON. No se usa una tabla de distancias.

**No regenerar el grafo.** No ejecutes `generate_mexico_graph.py` sobre esta entrega: sobrescribiría el HTML y sus controles. No se modificaron 4-NN, MST ni el dump GeoNames. El generador y el dump permanecen en el proyecto original; esta entrega solo contiene lo necesario para buscar y visualizar rutas.

## Verificación y evidencias

```powershell
python -m unittest -v test_routes.py
python find_route.py --from-city Tijuana --to Cancún --ucs
```

Las siete pruebas verifican optimalidad contra un Dijkstra independiente (cuatro parejas y 60 casos adicionales), validez del camino, consistencia de la heurística, vecinos en ambos sentidos, origen igual a destino, duplicados, entradas desconocidas y un grafo desconectado.

`evidencias/` contiene capturas reales del navegador de dos rutas, una vista móvil, salidas completas del CLI para las cuatro parejas, resultados A*/UCS en JSON, registros de pruebas y el SHA-256 que confirma que el JSON entregado es idéntico al original. La verificación en Edge también comprobó paridad Python/JavaScript, número de nodos y aristas dibujados, controles y manejo de errores.

El reporte breve está en `REPORTE.md`.

Corrección de apertura: el HTML ya no depende de archivos JavaScript externos y el botón no envía un formulario. Clic y Enter calculan la ruta sin recargar la página, incluso cuando se abre el HTML solo.
