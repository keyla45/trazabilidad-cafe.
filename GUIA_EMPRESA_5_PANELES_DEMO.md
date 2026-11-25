# CaféTrace — Empresa Origen y Taza (escenario DEMO)

## Objetivo

Simular las operaciones de una sola empresa cafetera, con cinco áreas conectadas al mismo lote: Agricultor/Proveedor, Producción/Logística, Almacén, Distribución y Clientes/Tienda. La empresa, las personas, los precios, las ubicaciones y los eventos de ejemplo son ficticios y no constituyen evidencia de una operación real.

## Accesos

- Administración: `http://127.0.0.1:8000/` (usuario administrador)
- Empresa y cinco paneles: `http://127.0.0.1:8000/empresa/`
- Panel Agricultor: `/empresa/area/proveedor/`
- Panel Producción: `/empresa/area/produccion/`
- Panel Almacén: `/empresa/area/almacen/`
- Panel Distribución: `/empresa/area/distribucion/`
- Panel Tienda: `/empresa/area/tienda/`
- Catálogo público, sin login: `/explorar/`

## Carga repetible de información ficticia

Ejecutar en PowerShell desde la carpeta CaféTrace:

```
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py cargar_empresa_demo
.\venv\Scripts\python.exe manage.py test cadena
.\venv\Scripts\python.exe manage.py runserver
```

`cargar_empresa_demo` utiliza también `cargar_demo_mrp` y `cargar_catalogo_marcas` para crear el escenario de origen, materiales, recetas, planificación, lotes, marcas y precios. Identificadores únicos DEMO permiten volver a ejecutarlo sin generar las mismas entradas varias veces.

## Simulación guiada para exposición

1. Iniciar sesión como administrador, entrar a **Empresa DEMO**, elegir el lote DEMO-ESP-01.
2. Agricultor: mostrar productor, finca, cosecha y eventos de beneficio y secado.
3. Producción: mostrar etapas del lote y planes MRP de empaque; abrir los registros de procesos.
4. Almacén: mostrar entradas, salidas, saldo y materiales de empaque.
5. Distribución: mostrar pedido, destino y operación de transporte vinculada.
6. Clientes/Tienda: mostrar puntos de venta ficticios, marcas, gramajes y precios registrados.
7. Abrir el QR: debe llevar a la ficha pública del mismo lote. En un celular que use la misma Wi-Fi que la computadora, iniciar el servidor con el script `INICIAR_CAFETRACE_RED.ps1`; desde Internet se requiere alojamiento público.

El selector de lote permite observar las diferencias en procesos y estados. Los botones "Abrir función" conducen a los formularios y listados del sistema. Las vistas DEMO son de lectura: no crean ventas ni movimientos al navegar.

## Diferencia entre DEMO y validación real

Los datos del escenario fueron simulados para enseñar el uso del sistema. Para la rúbrica se necesitan aparte registros presenciales de usuarios reales, tiempos de tarea, conteos físicos, fotografías y videos del recorrido validado. No se deben copiar cifras DEMO en el informe como resultados obtenidos en campo.

## Protección de datos

El instalador `INSTALAR_EMPRESA_CINCO_DEMO.ps1` sustituye solo 7 archivos de vistas/URL/plantillas/CSS y crea respaldo de los existentes. No modifica SQLite, migraciones ni contraseñas. Antes de cambios grandes es conveniente realizar respaldo de toda la carpeta de proyecto.
