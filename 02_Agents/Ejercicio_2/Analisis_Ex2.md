# Ejercicio 2 — Descripción PEAS de agentes inteligentes

### 1. Asistente virtual de voz (Siri, Alexa, Google Assistant en altavoz inteligente)

- **Performance:** reconocimiento de voz correcto, latencia de respuesta, satisfacción del usuario, pocas activaciones accidentales.
- **Environment:** hogar u oficina, dispositivos IoT conectados y servicios en la nube.
- **Actuators:** bocina, encender/apagar dispositivos conectados, programar cosas en el dispositivo.
- **Sensors:** micrófonos, botones, cámara.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial y dinámico.

### 2. Robot aspirador doméstico
- **Performance:** porcentaje de piso limpio, ahorro de batería, cero golpes a los muebles, evitar caídas por escaleras.
- **Environment:** interior de una casa; hay muebles, mascotas y personas en movimiento.
- **Actuators:** motores de las ruedas, motor de succión, cepillos giratorios, regreso a la base.
- **Sensors:** sensores de proximidad, sensores de impacto (parachoques), cámara o láser (LIDAR) para mapeo, detector de desniveles.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial y dinámico.

### 3. Sistema de recomendación de streaming
- **Performance:** cantidad de clics en las recomendaciones, tiempo total que el usuario pasa consumiendo el contenido, retención de suscripciones.
- **Environment:** plataforma digital (app o página web) con un catálogo en constante cambio y millones de usuarios.
- **Actuators:** mostrar portadas de series/música en la pantalla, enviar notificaciones, reproducir el siguiente episodio automáticamente.
- **Sensors:** historial de reproducciones, clics, "me gusta", tiempo de visualización, búsquedas.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial y dinámico.

### 4. Vehículo autónomo en ciudad
- **Performance:** seguridad (cero accidentes), respeto a las leyes de tránsito, tiempo de llegada, viaje suave (sin frenones).
- **Environment:** calles de la ciudad; hay tráfico impredecible, peatones, semáforos y cambios de clima.
- **Actuators:** volante, acelerador, freno, direccionales, claxon.
- **Sensors:** cámaras, radares, LIDAR, GPS, micrófonos.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial, dinámico y continuo.

### 5. Agente de trading algorítmico en bolsa
- **Performance:** ganancias monetarias (ROI), rapidez para ejecutar órdenes, evitar pérdidas grandes.
- **Environment:** mercado financiero digital; interactúa con otros algoritmos, reguladores y noticias del mundo real que cambian los precios en milisegundos.
- **Actuators:** comprar acciones, vender acciones, cancelar órdenes.
- **Sensors:** gráficas de precios en tiempo real, noticias financieras vía API, saldo de la cuenta.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial, dinámico y continuo.

### 6. Sistema de diagnóstico médico asistido por IA
- **Performance:** precisión en el diagnóstico (sin falsos positivos), rapidez para entregar resultados, coincidencia con la opinión del médico humano.
- **Environment:** clínica u hospital; se basa en expedientes médicos y estudios clínicos de los pacientes.
- **Actuators:** generar un reporte de diagnóstico, marcar anomalías en una radiografía (con colores), enviar alertas de riesgo.
- **Sensors:** radiografías o resonancias magnéticas, resultados de laboratorio, síntomas escritos en el expediente.

*Clasificación del entorno:* parcialmente observable, estocástico y episódico (si solo revisa un examen a la vez).

### 7. Dron de inspección de infraestructura
- **Performance:** precisión para encontrar grietas o fallas, área total revisada, ahorro de batería, cero choques.
- **Environment:** puentes, edificios o tuberías; el espacio físico puede tener obstáculos, viento o poca luz.
- **Actuators:** motores de las hélices para volar, cámara giratoria, luces.
- **Sensors:** cámaras (normales o térmicas), sensores de distancia, GPS, sensor de batería.

*Clasificación del entorno:* parcialmente observable, estocástico y secuencial.

### 8. Agente jugador de ajedrez
- **Performance:** partidas ganadas, nivel alcanzado (Elo), hacer jugadas dentro del límite de tiempo.
- **Environment:** tablero de ajedrez con reglas matemáticas estrictas; el único factor externo es el oponente.
- **Actuators:** mover piezas en la pantalla, ofrecer un empate.
- **Sensors:** conocer la posición exacta de todas las piezas en el tablero, ver el reloj de tiempo restante.

*Clasificación del entorno:* totalmente observable, determinista, secuencial y estático (durante su turno para pensar).
