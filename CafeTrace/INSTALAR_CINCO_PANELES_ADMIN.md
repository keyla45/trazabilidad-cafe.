# CaféTrace – cinco paneles por área

## Cambios
- El superusuario accede al centro privado de las cinco áreas.
- Usuarios de otros roles entran automáticamente en su primera área autorizada.
- Agricultor/proveedor incluye accesos a cosecha, recepción, beneficio y secado; producción se centra en trilla, tostión, empaque y MRP.
- Almacén, distribución y clientes/tienda tienen sus tableros de acciones.
- El menú general se simplificó; modelos y rutas previas se mantienen.
- La aplicación sigue usando los registros reales y los datos DEMO existentes.

## Instalación
1. Detén el servidor y guarda copia de db.sqlite3 y del proyecto.
2. Reemplaza código del proyecto con la carpeta CafeTrace del ZIP sin borrar venv, db.sqlite3 ni migraciones existentes.
3. Ejecuta: `.\venv\Scripts\python.exe -m pip install -r requirements.txt`
4. Ejecuta: `.\venv\Scripts\python.exe manage.py check`
5. Ejecuta: `.\venv\Scripts\python.exe manage.py migrate`
6. Ejecuta: `.\venv\Scripts\python.exe manage.py runserver`

No se agregaron modelos ni migraciones; las cinco áreas son una reorganización de vistas y menús.
