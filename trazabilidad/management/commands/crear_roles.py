from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from trazabilidad.permissions import ROLE_NAMES
class Command(BaseCommand):
    help="Crea los cinco grupos de acceso de CaféTrace."
    def handle(self,*args,**kwargs):
        for name in ROLE_NAMES: Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Roles disponibles: "+", ".join(ROLE_NAMES)))
