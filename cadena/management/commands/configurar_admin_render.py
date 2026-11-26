import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea o recupera el administrador de CafeTrace en Render."

    def handle(self, *args, **options):
        username = os.environ.get("CAFETRACE_ADMIN_USERNAME", "admin")
        password = os.environ.get("CAFETRACE_ADMIN_PASSWORD")

        if not password:
            self.stdout.write(
                "No se configuro el administrador: falta CAFETRACE_ADMIN_PASSWORD."
            )
            return

        User = get_user_model()

        usuario, creado = User.objects.get_or_create(
            username=username
        )

        usuario.set_password(password)
        usuario.is_active = True
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Administrador de CafeTrace configurado correctamente."
            )
        )
