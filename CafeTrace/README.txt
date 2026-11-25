CAFÉTRACE - APLICATIVO DE PRUEBA
================================

Proyecto 6: Trazabilidad y calidad en la cadena del café - UPEC.

TECNOLOGÍAS
- Python
- Django
- SQLite
- HTML/CSS
- QR mediante qrcode

FUNCIONES INCLUIDAS
1. Página principal y panel básico.
2. Registro de productores.
3. Registro/consulta de fincas desde Admin.
4. Registro de lotes de café.
5. Código único de trazabilidad generado automáticamente.
6. Datos básicos de beneficio, secado y fermentación.
7. Registro inicial de calidad/catación desde Admin.
8. Línea de tiempo de trazabilidad.
9. Generación de QR para cada lote.
10. Página pública del lote accesible mediante QR.
11. Panel administrativo de Django.
12. Base de datos SQLite.

INSTALACIÓN EN WINDOWS / VISUAL STUDIO
--------------------------------------

1. Abre esta carpeta en Visual Studio Code o Visual Studio.

2. Abre una terminal en la carpeta donde está manage.py.

3. Crea un entorno virtual:
   python -m venv venv

4. Actívalo en Windows:
   venv\Scripts\activate

5. Instala las dependencias:
   pip install -r requirements.txt

6. Crea las tablas:
   python manage.py makemigrations
   python manage.py migrate

7. Crea un usuario administrador:
   python manage.py createsuperuser

8. Inicia el servidor:
   python manage.py runserver

9. Abre en el navegador:
   http://127.0.0.1:8000/

10. Panel administrativo:
   http://127.0.0.1:8000/admin/

IMPORTANTE
-----------
Esta es la primera versión de prueba. No incluye todavía sensores IoT,
predicción con Machine Learning, Power BI, Odoo ni una aplicación móvil.
Esas funciones se pueden integrar después de comprobar que esta base
funciona correctamente.

FLUJO DE PRUEBA RECOMENDADO
---------------------------
A. En /admin/ crea un Productor.
B. En /admin/ crea una Finca asociada al productor.
C. En Inicio -> Nuevo lote, crea un lote.
D. El sistema genera un código CAF-AÑO-XXXXXX.
E. Abre el detalle del lote y observa el QR.
F. El QR lleva a la vista pública del lote.
G. En /admin/ registra la evaluación de calidad y eventos adicionales.

NOTA
----
La base de datos db.sqlite3 se crea después de ejecutar migrate.
