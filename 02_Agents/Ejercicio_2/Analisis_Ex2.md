# Ejercicio 2 — Descripción PEAS de agentes inteligentes

### 1. Asistente virtual de voz

- **Performance:** reconocimiento de voz correcto, latencia de respuesta, satisfacción del usuario, pocas activaciones accidentales.
- **Environment:** hogar u oficina, dispositivos IoT conectados y servicios en la nube.
- **Actuators:** bocina, encender/apagar dispositivos conectados, programar cosas en el dispositivo.
- **Sensors:** micrófonos, botones, cámara.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial y dinámico.

### 2. Robot aspirador doméstico
- **Performance:** porcentaje de piso limpio, ahorro de batería, cero golpes a los muebles, evitar caídas por escaleras.
- **Environment:** interior de una casa u oficina.
- **Actuators:** motores de las ruedas, motor de succión, cepillos giratorios.
- **Sensors:** sensores de proximidad, sensores de impacto; cámara o láser.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial y dinámico.

### 3. Sistema de recomendación de streaming
- **Performance:** pelis mas vistas, tiempo total de consumo, suscripciones.
- **Environment:** plataforma digital y usuarios.
- **Actuators:** mostrar series/pelis en la pantalla, enviar notificaciones.
- **Sensors:** historial de reproducciones, lsitas del usuario, búsquedas.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial y dinámico.

### 4. Vehículo autónomo en ciudad
- **Performance:** seguridad, respeto a las leyes de tránsito, tiempo de llegada.
- **Environment:** calles de la ciudad, peatones, semáforos.
- **Actuators:** volante, acelerador, freno, direccionales, claxon.
- **Sensors:** cámaras, radares, LIDAR, GPS, micrófonos.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial, dinámico y continuo.

### 5. Agente de trading algorítmico en bolsa
- **Performance:** ROI, rapidez para ejecutar órdenes, evitar pérdidas grandes.
- **Environment:** mercado financiero digital, noticias del mundo real, cambio de precios.
- **Actuators:** comprar acciones, vender acciones.
- **Sensors:** gráficas de precios, noticias financieras, saldo de la cuenta.

*Clasificación del entorno:* parcialmente observable, estocástico, secuencial, dinámico y continuo.

### 6. Sistema de diagnóstico médico asistido por IA
- **Performance:** precisión en el diagnóstico, rapidez para entregar resultados, coincidencia con la opinión del médico humano.
- **Environment:** clínica u hospital.
- **Actuators:** generar un reporte de diagnóstico, marcar anomalías en estudios, enviar alertas de riesgo.
- **Sensors:** estudios médicos, resultados de laboratorio, síntomas.

*Clasificación del entorno:* parcialmente observable, estocástico y episódico (si solo revisa un examen a la vez).

### 7. Dron de inspección de infraestructura
- **Performance:** precisión para encontrar fallas, área revisada, no chocar.
- **Environment:** construcciones, edificios o casas.
- **Actuators:** motores de las hélices, cámara, luces.
- **Sensors:** cámara, sensores de distancia, GPS.

*Clasificación del entorno:* parcialmente observable, estocástico y secuencial.

### 8. Agente jugador de ajedrez
- **Performance:** partidas ganadas.
- **Environment:** tablero de ajedrez.
- **Actuators:** mover piezas.
- **Sensors:** conocer la posición de todas las piezas en el tablero, ver el reloj de tiempo restante.

*Clasificación del entorno:* totalmente observable, determinista, secuencial y estático (durante su turno para pensar).
