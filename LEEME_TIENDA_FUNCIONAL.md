# CaféTrace — Tienda y clientes: versión funcional visual

Esta actualización desarrolla **las seis tarjetas de Clientes y tienda** sobre la versión existente de **Cinco Áreas 2026**.

- **Catálogo de cafés:** busca por lote, finca y variedad, con acceso a la ficha.
- **Puntos de venta:** lista de establecimientos ficticios o reales, con alta autorizada.
- **Nueva venta:** formulario Django. El perfil `Bodega` o el administrador pueden registrar. Otros roles consultan actividad sin poder alterar ventas.
- **Presentaciones:** listado de productos (SKU, peso, tipo, unidades y precio), vinculado a trazabilidad pública.
- **Pedidos comerciales:** actividad de ventas con estado. La confirmación autorizada crea un pedido **pendiente**. El stock no se descuenta hasta registrar despacho.
- **QR para clientes:** galería con acceso a la ficha pública existente y al código QR del lote.

## Requisitos

El código corresponde a la versión previa `CafeTrace_UPEC_5_Areas_Experiencia_2026.zip` con su app `cadena` y `trazabilidad` instaladas. Ejecuta la instalación en la carpeta actual **CafeTrace**, sin sustituir tu base SQLite. La nueva versión no necesita migraciones porque no incorpora modelos.

## Instalación desde terminal PowerShell

Detén el servidor con Ctrl+C. Descarga `CafeTrace_UPEC_Tienda_Funcional_Visual.zip`. El script `INSTALAR_TIENDA_FUNCIONAL.ps1` se incluye en el archivo completo, pero puedes usar directamente el bloque de instalación entregado en el chat; hará copia de seguridad antes de reemplazar archivos.

Verifica con ` .\venv\Scripts\python.exe manage.py check ` y luego ejecuta ` .\venv\Scripts\python.exe manage.py runserver `.

## Pruebas manuales

1. Inicia sesión con admin y abre `/areas/tienda/`.
2. Prueba las tarjetas Catálogo, Puntos de venta, Presentaciones y QR.
3. Abre Nueva venta y registra una operación DEMO (si corresponde al entorno de prueba).
4. Confirma la venta una sola vez. Debe generarse un pedido pendiente.
5. Abre la sección de Distribución para verificar el pedido. Prueba QR: abre la página pública de un lote.
6. Inicia sesión como Cliente y verifica que pueda consultar, sin poder registrar o confirmar ventas.

## Límites

No contiene pasarela de pago, facturación fiscal, geolocalización real, una tienda publicada en internet ni conexión física a sensores. Los datos DEMO del comando `cargar_demo_mrp` son ficticios y deben presentarse como tales.
