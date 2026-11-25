# CaféTrace — Asistente y guía de operación (ampliación)

## Qué incluye
- Chatbot de reglas y datos **de solo lectura** que responde por inventario, MRP, pedidos, origen, procesos, ventas, códigos QR e incidencias.
- Búsqueda de un lote por código exacto `DEMO-ESP-01`, con resumen de origen, estado, etapas efectivamente registradas y saldo documental.
- Guía interactiva de las cinco áreas vinculadas a las pantallas del sistema.
- Preguntas de ejemplo, sugerencias de seguimiento y acceso directo al registro relacionado.
- Dictado de voz si el navegador lo soporta: reconoce la pregunta, la coloca en el formulario y el usuario confirma antes de enviarla.
- API JSON `/api/asistente/?q=...` autenticada, exclusiva de personal autorizado.
- Diez pruebas nuevas de consultas, código inexistente y protección frente a clientes/usuarios anónimos.

## Limitaciones honestas
Este asistente no usa un modelo generativo, no actúa autónomamente y no realiza transacciones. No es una integración con Odoo. Los registros identificados DEMO son ficticios. El reconocimiento de voz depende del navegador y puede usar sus servicios de voz; no implica funcionamiento completamente local ni modo sin Internet.

## Validación con usuarios (evidencia real por obtener)
Pida a 3–5 personas realizar tareas: buscar el lote DEMO-ESP-01, consultar el saldo, encontrar un pedido, explicar cómo verificar el QR y navegar a Producción. Cronometre tiempo, errores, pasos y éxito; recoja una encuesta SUS completa si se va a reportar puntaje SUS. Registre fecha, rol y consentimiento, y tome capturas/video con autorización. No convierta resultados DEMO en evidencia empírica.

## Pruebas y acceso
Desde `C:\Users\PC_1\Desktop\CafeTrace` ejecutar:
```
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test cadena.tests_asistente_mejorado
.\venv\Scripts\python.exe manage.py test cadena
.\venv\Scripts\python.exe manage.py runserver
```
Abra `http://127.0.0.1:8000/herramientas/` con un usuario administrativo.

## Presentación el 1 de diciembre
Inicie con cinco áreas y lote DEMO, abra `/herramientas/`, consulte stock, lote, pedidos y MRP, use dictado en navegador compatible, siga el enlace a una ficha real del lote y explique que la API consulta datos. Mencione explícitamente qué pruebas automatizadas y pruebas presenciales fueron superadas.
