# CaféTrace — Dos accesos y pasaporte QR

## Qué cambia
- `/acceder/`: acceso administrativo con contraseña y enlace directo a explorar.
- `/explorar/`: catálogo público sin contraseña, filtros y presentaciones/precios disponibles en BD.
- `/explorar/cafe/<id>/`: pasaporte público con etapas registradas, eventos, calidad aprobada, precios y QR.
- `/explorar/cafe/<id>/qr/`: imagen PNG QR del pasaporte anterior.
- El menú del administrador conserva todas las cinco áreas y añade acceso al catálogo público.

## Instalación sin perder datos
1. Guarda el ZIP descargado. Descomprímelo o usa `Expand-Archive`.
2. En la carpeta de tu proyecto Django, ejecuta `& "RUTA_EXTRAIDA\CafeTrace\INSTALAR_CATALOGO_QR.ps1"`.
3. Ejecuta ` .\venv\Scripts\python.exe manage.py check`.
4. Ejecuta ` .\venv\Scripts\python.exe manage.py test cadena`.
5. Para datos DEMO ` .\venv\Scripts\python.exe manage.py cargar_empresa_demo` (opcional, repetible).
6. Para abrir en la PC ` .\venv\Scripts\python.exe manage.py runserver` y ve a `http://127.0.0.1:8000/explorar/`.
7. Para QR en celular: detén el servidor y usa ` .\INICIAR_CAFETRACE_RED.ps1`. En el móvil conectado a la misma Wi-Fi visita la URL `http://IP_DE_LA_PC:8000/explorar/` que se muestra en terminal y escanea el QR. Permite acceso por firewall en redes privadas.

Los códigos QR NO funcionan en otros dispositivos si apuntan a `127.0.0.1`. La variable de entorno `CAFETRACE_PUBLIC_BASE_URL` se configura temporalmente al iniciar el servidor por red local. Para exponer el QR públicamente desde Internet es necesario hosting con dominio HTTPS, base de datos persistente, `ALLOWED_HOSTS`, seguridad, política de privacidad y un despliegue apropiado (no `runserver`).

No contiene pagos reales ni una tienda comercial desplegada. Los precios y existencias DEMO son ficticios. No publica correos, teléfonos ni coordenadas de productores. La calidad sensorial solo se muestra si está aprobada para publicación.
