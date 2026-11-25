# CaféTrace UPEC — ampliación del capítulo 6

Esta versión **conserva el proyecto original** y añade formularios, modelos y páginas para recepción, procesamiento, sensores, inventario, pedidos y experimentos E1–E3.

## Ejecución en Windows (PowerShell)

```powershell
cd CafeTrace
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations trazabilidad
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra http://127.0.0.1:8000/admin/ e inicie sesión; después visite http://127.0.0.1:8000/ . Los módulos nuevos requieren la misma sesión de administrador. Si PowerShell impide activar el entorno, utilice `.venv\Scripts\python.exe` en lugar de `python`.

## Módulos ampliados

- Productores, fincas, lotes, trazabilidad pública y QR: existentes, conservados.
- Recepción: peso, humedad y defectos por lote.
- Procesos: beneficio, fermentación, secado, trillado, tueste y empaque, con mediciones.
- Sensores: lecturas manuales o marcadas como IoT, **sin conexión MQTT automática todavía**.
- Calidad: edición de catación desde el detalle de lote.
- Inventario: movimientos de entrada/salida y prevención de saldo negativo en el formulario de salida.
- Pedidos: registro, preparación, despacho, entrega y bandera CEDI.
- Indicadores: conteos y promedio descriptivo calculado con los registros existentes.
- Experimentos: registro de medidas observadas para E1, E2, E3, distinguiendo base y solución.
- API autenticada: `/api/lotes/` y `/api/cedi/despacho/<pedido_id>/` (formato preliminar, **aún no validado con el contrato real del CEDI**).

## Pendiente para cumplir integralmente el capítulo 6

1. Integración real con Odoo (compras, fabricación, inventario y ventas) y comercio digital.
2. ESP32, MQTT/Mosquitto y Node-RED para captación automática y seguimiento del sensor.
3. Modelo predictivo scikit-learn con entrenamiento y evaluación en lotes no vistos (mínimo 10 lotes según el documento).
4. Agente de IA de solo lectura y auditoría con permisos mínimos.
5. Tableros Power BI, GIS/QGIS, integración final con el CEDI y contrato de datos acordado.
6. Seguridad para producción: SECRET_KEY de entorno, DEBUG=False, HTTPS, control de permisos por rol, pruebas y trazabilidad de ediciones.
7. Validación experimental con datos reales; **no se suministran ni se inventan resultados**.

## Nota de pruebas

Los archivos Python superaron la comprobación de sintaxis (`compileall`). No se pudo ejecutar `manage.py check`, ni migraciones, ni pruebas HTTP porque este entorno no contiene Django y carece de acceso a los paquetes requeridos. Ejecute los comandos indicados en su computador. Se recomienda hacer una copia de seguridad antes de migrar una base de datos existente.
