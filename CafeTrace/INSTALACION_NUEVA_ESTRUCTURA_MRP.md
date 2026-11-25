# CafeTrace UPEC · Arquitectura nueva de cinco áreas

Este proyecto reorganiza la interfaz según el documento **TICS aplicativo café.docx**, capítulos 6.1, 6.3 y 6.5. El sistema ahora prioriza cinco áreas: Agricultor/Proveedor, Producción y Logística, Almacén, Distribución y Tienda. Lotes, calidad y QR son funciones transversales. El sistema utiliza los modelos de trazabilidad originales y una app nueva, `cadena`, para materiales, planes MRP, puntos de venta y operaciones de comercialización.

## Instalación segura en Windows PowerShell

1. Guarda una copia **completa** de tu carpeta `CafeTrace`, especialmente `db.sqlite3`, `venv` y `trazabilidad/migrations`. No borres los archivos anteriores.
2. Descomprime el ZIP. Copia los archivos sobre tu proyecto existente, conservando `db.sqlite3`, `venv` y todas las migraciones históricas de `trazabilidad`.
3. Desde la terminal abierta en `C:\Users\PC_1\Desktop\CafeTrace`, ejecuta cada línea por separado:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py crear_roles
.\venv\Scripts\python.exe manage.py cargar_demo_mrp
.\venv\Scripts\python.exe manage.py runserver
```

**Importante:** La app `cadena` incluye su migración inicial `0001_initial.py`; NO necesita `makemigrations` para esa app. Si trabajas en una instalación totalmente nueva sin la historia de `trazabilidad`, antes de `migrate` ejecuta `manage.py makemigrations trazabilidad` y verifica que se creó su migración inicial. En una instalación antigua, conserva los archivos históricos de migraciones para evitar inconsistencias.

4. Visita `http://127.0.0.1:8000/`, inicia sesión con tu cuenta existente y explora las cinco áreas. Desde la tienda puedes crear y confirmar una venta; eso genera un pedido pendiente para distribución. El stock de café se descuenta cuando se despacha desde Pedidos, no al confirmar la venta.

## Qué funciona y qué no

- Registro de origen, recepción, transformación, calidad, lotes, movimientos y pedido: reutiliza funciones originales.
- Materiales, movimientos, recetas por kilogramo, planes MRP, puntos de venta, ventas e incidencias: nuevos modelos y formularios.
- Requerimientos: cálculo simple por receta y cantidad planificada, menos stock disponible, más stock mínimo. No incluye calendario MRP detallado, recepciones programadas, compras automáticas ni lista multinivel.
- QR: cada lote tiene su imagen QR y ficha pública del proceso. QR local (`127.0.0.1`) solo abre desde el mismo equipo salvo configuración de red/servidor.
- Datos DEMO: completamente ficticios, independientes de la evidencia científica. El comando intenta ser repetible y no elimina los registros existentes.
- Los experimentos del documento **actualizado** son E1 rastreo del lote, E2 exactitud del inventario y E3 seguimiento de pedidos. Los experimentos de humedad/predicción del documento antiguo NO se presentan como evidencia de esta versión.
- Sensores IoT, predicción IA, Odoo y Power BI no son requisitos operativos de esta versión y no se consideran integrados.

## Precauciones

No despliegues el servidor de desarrollo públicamente. Configura SECRET_KEY propia, DEBUG=False y HTTPS en un entorno productivo. Prueba primero la actualización sobre una copia de la base de datos.

## Diferencia entre el documento principal y su anexo

La sección **6.5.8**, página 24 del nuevo documento, establece E1 localización de lotes, E2 control de inventario y E3 seguimiento de pedidos. El anexo final todavía hace referencia a experimentos anteriores de humedad, predicción y QR. Esta versión del aplicativo sigue la sección metodológica **6.5.8**, por ser la definición actual y detallada. Conviene corregir el anexo del documento antes de presentarlo.

## Separación del proyecto antiguo

Se conserva la carpeta `trazabilidad`, sus datos y URLs antiguas para compatibilidad. El nuevo menú centraliza las operaciones en 5 áreas y utiliza `cadena` como app complementaria de materiales, MRP y tienda. Las páginas antiguas pueden seguir existiendo por URL directa, pero no son la navegación principal. **No elimines modelos antiguos ni migraciones que ya fueron aplicadas a tu BD.**
