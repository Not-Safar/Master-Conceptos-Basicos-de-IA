# Análisis del Comportamiento de los Agentes en el Mundo del Wumpus

## 1. Desempeño de los agentes en el mapa
*   Únicamente el Utility Agent logró extraer el oro y salir vivo, finalizando la partida en 30 pasos con un puntaje positivo de 960.
*   El Reflex Agent, el Model Agent y el Goal Agent fracasaron. Se quedaron estancados girando sobre su propio eje hasta alcanzar el límite máximo de 200 pasos, terminando con un puntaje de -200.
*   El Learning Agent falló al ejecutar la acción de escalar apenas en el primer paso, abandonando la cueva sin el oro con un puntaje de -1.

## 2. Análisis del agente de reflejo simple
El agente de reflejo simple toma decisiones basándose exclusivamente en su percepción actual, sin conservar memoria de los pasos anteriores. Al toparse con la brisa generada por el pozo ubicado en la coordenada [2, 2], sus reglas preprogramadas le indican que no debe avanzar hacia el peligro. Debido a que no puede construir un mapa mental para recordar qué casillas previas eran seguras o planear un rodeo, el agente se queda atrapado en un bucle infinito ejecutando acciones de giro (TurnRight o TurnLeft) para evitar la muerte, agotando así sus turnos.

## 3. Cómo afecta la ubicación de los pozos al agente basado en modelo

*   **Si el pozo está muy cerca:** Al tener un pozo cerca, el agente siente la brisa en cuanto da el primer paso. Como su "mapa interno" está prácticamente vacío al inicio de la partida, no tiene cómo deducir en qué casilla exacta está el hoyo. Ante la falta de rutas 100% seguras, el agente prefiere no arriesgarse y se queda paralizado dando vueltas hasta que se le acaban los turnos.
*   **Si se aleja el pozo:** Por el contrario, si se mueve el pozo más lejos, le damos espacio al agente para caminar y confirmar que las primeras casillas son seguras. Para cuando finalmente siente una brisa, ya exploró lo suficiente como para ir descartando opciones en su mente, descubrir por simple lógica dónde está escondido el pozo, y tomar un camino alternativo para llegar tranquilamente al oro.
