# Protocolo de validación con usuarios — CaféTrace

## Preparación
1. Iniciar el servidor y comprobar el enlace de acceso desde otro dispositivo.
2. Crear cuentas de prueba sin reutilizar contraseñas personales.
3. Identificar los lotes DEMO y explicar que son ficticios.
4. Pedir consentimiento antes de grabar voz, pantalla o fotografías. No recolectar datos sensibles.

## Tareas (registrar tiempo en segundos, completada Sí/No, errores y comentarios)
- **T1 – Agricultor:** ingresar y consultar la ficha de un lote vinculado a finca.
- **T2 – Producción:** localizar un proceso, identificar su estado y responsable.
- **T3 – Almacén:** localizar un producto y verificar existencia según movimientos.
- **T4 – Distribución:** identificar un pedido pendiente y su estado de entrega.
- **T5 – Tienda:** localizar presentación, precio y punto de venta ficticio.
- **T6 – QR:** abrir el pasaporte de un lote y describir su origen y etapas realmente registradas.
- **T7 – Asistente:** preguntar por un pedido o inventario y seguir el enlace proporcionado.
- **T8 – Voz:** dictar una consulta en navegador compatible; si no está disponible registrar “No disponible”.
- **T9 – API:** con rol autorizado abrir `/api/resumen/` y comprobar JSON; con Cliente comprobar denegación.

## Pruebas negativas
Código de lote duplicado, salida mayor al stock, campos obligatorios faltantes, acceso no autorizado y lote inexistente. No modificar datos reales para provocar errores: utilizar una base de prueba.

## Indicadores de resultados
- Tasa de éxito = tareas completadas / tareas intentadas × 100.
- Tiempo de rastreo = segundos desde la solicitud hasta localizar origen y eventos del lote.
- Exactitud de inventario = comparar registros y conteos físicos mediante criterio definido previamente.
- Pedidos correctos = pedidos con cantidad y producto solicitados = preparados/despachados, según evidencia.
- Si se aplica SUS, usar el cuestionario íntegro y la forma oficial de puntuación; no calcular SUS de preguntas informales.

## Formato de evidencia
Nombre de archivo: `Tarea_T1_Usuario_U01_2026-11-XX.png` (ejemplo). Usar códigos anónimos U01, U02, etc.
Cada persona participante debe autorizar la captura y poder negarse sin impedir su participación en las pruebas.
