from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# No crea claves ni cambia contraseñas: solo actualiza cuentas de prueba existentes.
PERFILES={
 'agricultor1':('Juan','Pérez','agricultor1@cafetrace.demo','Productor'),
 'produccion1':('Carlos','Méndez','produccion1@cafetrace.demo','Producción'),
 'almacen1':('Lucía','Herrera','almacen1@cafetrace.demo','Almacén'),
 'distribuidor1':('David','Rosero','distribuidor1@cafetrace.demo','Distribución'),
 'conductor1':('David','Rosero','conductor1@cafetrace.demo','Distribución'),
 'cliente1':('Andrea','Rosales','cliente1@cafetrace.demo','Tienda'),
}
class Command(BaseCommand):
    help='Asigna identidad y área a usuarios de práctica existentes, sin modificar sus contraseñas.'
    def handle(self,*args,**kwargs):
        User=get_user_model()
        for username,(nombre,apellido,correo,area) in PERFILES.items():
            u=User.objects.filter(username=username,is_superuser=False).first()
            if not u:
                self.stdout.write(f'No existe {username}: omitido.')
                continue
            u.first_name=nombre;u.last_name=apellido;u.email=correo;u.save(update_fields=['first_name','last_name','email'])
            group,_=Group.objects.get_or_create(name=area)
            u.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f'{username} → {nombre} {apellido} / {area}'))
        self.stdout.write('Las contraseñas no se modificaron. Los correos .demo son ficticios.')
