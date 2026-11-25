# CaféTrace — catálogo multimarca y QR por presentación

## Qué contiene

- 8 cafés de ejemplo (variedades y especies distintas).
- 6 marcas ficticias.
- 48 SKU, incluidos 250 g, 500 g y 1.000 g con precios de demostración.
- Fichas públicas por presentación con lote, finca, historia, proceso, trazabilidad y QR.
- Filtros por marca, especie, proceso y formato.
- En Django Admin: gestión de marcas y SKU del catálogo.

**No se procesan pagos. Los precios, fincas, marcas y movimientos DEMO son ficticios.**

## Instalación sin borrar datos

1. Hacer respaldo de `db.sqlite3` y la carpeta del proyecto.
2. Detener servidor con Ctrl+C.
3. Ejecutar `INSTALAR_CATALOGO_MARCAS.ps1` desde la carpeta actual de CafeTrace, tras extraer el ZIP.
4. Ejecutar, individualmente:

```powershell
.\venv\Scripts\python.exe manage.py makemigrations cadena
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py cargar_catalogo_marcas
.\venv\Scripts\python.exe manage.py test cadena.tests_catalogo
.\venv\Scripts\python.exe manage.py runserver
```

5. Ver `/explorar/` desde un navegador.

## QR en celular

Ejecutar `INICIAR_CAFETRACE_RED.ps1` del proyecto de red local original, abrir la dirección mostrada desde el celular con el mismo Wi-Fi. **No funcionará desde el celular un QR que codifica `127.0.0.1`.** Un QR público para cualquier red requiere un servidor desplegado con URL HTTPS. No exponer Django runserver directamente a Internet.

## Compatibilidad

El instalador reemplaza los modelos de la aplicación `cadena` de la base indicada. Si has agregado modelos propios después, se deben conciliar los cambios antes de reemplazar archivos. No copie el contenido de la carpeta `migrations` del ZIP sobre sus migraciones actuales. El comando `makemigrations` creará la migración en la instalación del usuario.
