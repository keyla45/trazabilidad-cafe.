from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from trazabilidad.permissions import ROLE_NAMES

class Command(BaseCommand):
    help = "Crea un usuario de CaféTrace con un rol. La contraseña se introduce sin mostrarla."
    def add_arguments(self, parser):
        parser.add_argument("usuario")
        parser.add_argument("rol", choices=ROLE_NAMES)
    def handle(self, *args, **opts):
        from getpass import getpass
        User=get_user_model()
        if User.objects.filter(username=opts["usuario"]).exists():
            raise CommandError("El usuario ya existe.")
        clave=getpass("Contraseña: ")
        clave2=getpass("Confirmar contraseña: ")
        if not clave or clave != clave2:
            raise CommandError("Las contraseñas no coinciden o están vacías.")
        user=User.objects.create_user(username=opts["usuario"],password=clave)
        grupo,_=Group.objects.get_or_create(name=opts["rol"])
        user.groups.add(grupo)
        self.stdout.write(self.style.SUCCESS(f"Usuario {user.username} creado con rol {grupo.name}."))
