"""Escenario empresarial ficticio, repetible y sin eliminación de datos reales."""
from datetime import timedelta
from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from trazabilidad.models import (Productor,Finca,Lote,EventoTrazabilidad,EtapaEspecial,
    ProcesoCafe,ControlCalidad,Pedido,Transporte,MovimientoInventario,PresentacionCafe)
from cadena.models import PuntoVenta,VentaTienda,Incidencia,PlanProduccion

STAFF = [
    ('agricultor1','Juan','Pérez','Productor','Agricultor / proveedor'),
    ('produccion1','Carlos','Méndez','Producción','Operario de tostión'),
    ('almacen1','Lucía','Herrera','Almacén','Encargada de bodega'),
    ('distribuidor1','David','Rosero','Distribución','Coordinador logístico'),
    ('cliente1','Andrea','Rosales','Tienda','Encargada de tienda'),
]

class Command(BaseCommand):
    help = 'Carga una empresa cafetera ficticia con actores, lotes, producción, inventario y tienda conectados. Repetible.'

    @transaction.atomic
    def handle(self,*args,**options):
        # Normaliza la finca DEMO antes de cargar lotes para que la carga sea repetible.
        Finca.objects.filter(productor__identificacion='DEMO-ESP-PROD',
                             nombre='DEMO · Finca de especialidad').update(nombre='DEMO · Finca La Esperanza')
        call_command('cargar_demo_mrp', stdout=self.stdout)
        call_command('cargar_catalogo_marcas', stdout=self.stdout)
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        User=get_user_model()
        for username,nombre,apellido,rol,cargo in STAFF:
            user=User.objects.filter(username=username,is_superuser=False).first()
            if user:
                user.first_name=nombre;user.last_name=apellido
                user.email=f'{username}@cafetrace.demo'
                user.save(update_fields=['first_name','last_name','email'])
                grupo,_=Group.objects.get_or_create(name=rol)
                # Retirar solo el antiguo rol genérico de bodega para mantener la separación de áreas.
                if rol in ('Producción','Almacén','Distribución','Tienda'):
                    viejo=Group.objects.filter(name='Bodega').first()
                    if viejo:user.groups.remove(viejo)
                user.groups.add(grupo)
            else:
                self.stdout.write(f'Usuario {username} no existe; no se crea una contraseña de ejemplo.')
        prod=Productor.objects.filter(identificacion='DEMO-ESP-PROD').first()
        if prod:
            prod.nombre='DEMO · Juan Pérez (productor ficticio)'
            prod.comunidad='Zona cafetera simulada de Carchi'
            prod.save(update_fields=['nombre','comunidad'])
            Finca.objects.filter(productor=prod,nombre='DEMO · Finca de especialidad').update(
                nombre='DEMO · Finca La Esperanza', parroquia='Parcela demostrativa',
                canton='Tulcán',provincia='Carchi',altura_msnm=1920)
        now=timezone.now()
        base_date=now-timedelta(days=25)
        nombres={1:('Geisha','Lavado'),2:('Bourbon','Natural'),3:('Caturra','Honey'),4:('Typica','Anaeróbico')}
        for indice,(variedad,metodo) in nombres.items():
            lote=Lote.objects.get(codigo=f'DEMO-ESP-{indice:02d}')
            lote.variedad=variedad
            lote.notas=('DEMO · Café de la empresa simulada Origen y Taza. '
                'No corresponde a una finca, producción ni certificación real.')
            lote.save(update_fields=['variedad','notas'])
            inicio=base_date+timedelta(days=indice)
            etapas=[('Finca','Cosecha selectiva y pesaje inicial','DEMO · Juan Pérez','Finca La Esperanza',-2),
                ('Recepción','Ingreso, pesaje e inspección del lote','DEMO · María Torres (acopio)','Centro de beneficio',0),
                ('Beneficio',f'Beneficio {metodo.lower()} con registro por lote','DEMO · María Torres (beneficio)','Centro de beneficio',1),
                ('Secado','Secado y verificación de humedad declarada','DEMO · María Torres (beneficio)','Zona de secado',4),
                ('Almacenamiento','Ingreso de café procesado a bodega','DEMO · Lucía Herrera','Bodega de origen',8)]
            if indice <= 2:
                etapas += [('Transporte','Despacho de café empacado a punto de venta','DEMO · David Rosero','Ruta simulada Tulcán',20),
                           ('Venta','Recepción demostrativa en la tienda','DEMO · Andrea Rosales','Tienda Origen y Taza',22)]
            for etapa,detalle,responsable,ubicacion,dias in etapas:
                ev,_=EventoTrazabilidad.objects.get_or_create(
                    lote=lote,etapa=etapa,detalle='DEMO EMPRESA · '+detalle,
                    defaults={'fecha':inicio+timedelta(days=dias),'responsable':responsable,'ubicacion':ubicacion})
            for e in EtapaEspecial.objects.filter(lote=lote,estado='Finalizada'):
                responsable=('DEMO · Carlos Méndez' if any(x in e.nombre.lower() for x in ('tost','trill','empaq','clasific'))
                              else 'DEMO · María Torres')
                e.responsable=responsable
                e.ubicacion='Planta Origen y Taza (simulada)'
                e.save(update_fields=['responsable','ubicacion'])
            ProcesoCafe.objects.filter(lote=lote).update(observaciones='DEMO EMPRESA · Registro técnico de simulación')
            PlanProduccion.objects.filter(lote=lote,es_demo=True).update(responsable='DEMO · Carlos Méndez')
            if indice<=2:
                MovimientoInventario.objects.filter(lote=lote,referencia__startswith='DEMO-').update(ubicacion='Bodega Origen y Taza · DEMO')
                Pedido.objects.filter(lote=lote,codigo_seguimiento__startswith='DEMO-').update(
                    destino='Tienda Origen y Taza, Tulcán (ubicación ficticia)')
                Transporte.objects.filter(lote=lote,placa__startswith='DEMO-').update(
                    transportista='DEMO · David Rosero',origen='Planta Origen y Taza',
                    destino='Tienda Origen y Taza, Tulcán (simulado)')
        # Tienda física y clientes de ejemplo, sin atribuir la dirección a un local existente.
        for nombre,tipo,ciudad in [
            ('DEMO · Tienda Origen y Taza','Tienda','Tulcán'),
            ('DEMO · Cafetería La Montaña','Cafetería','Tulcán'),
            ('DEMO · Mayorista Andino','Mayorista','Quito'),
            ('DEMO · Punto Aroma de Montaña','Minorista','Ibarra')]:
            PuntoVenta.objects.get_or_create(nombre=nombre,defaults={
                'tipo':tipo,'ciudad':ciudad,'direccion':'Punto de venta ficticio; sin dirección física real',
                'es_demo':True})
        punto=PuntoVenta.objects.get(nombre='DEMO · Tienda Origen y Taza')
        lote=Lote.objects.get(codigo='DEMO-ESP-01')
        VentaTienda.objects.get_or_create(numero='DEMO-EMPRESA-001',defaults={
            'punto_venta':punto,'lote':lote,'cantidad_kg':Decimal('2.000'),
            'precio_por_kg':Decimal('28.00'),'estado':'Reservado','es_demo':True})
        Incidencia.objects.get_or_create(titulo='DEMO EMPRESA · Inspección de empaques',defaults={
            'area':'Tienda','descripcion':'Simulación de una inspección de etiquetas y QR antes de exhibir.',
            'lote':lote,'estado':'Resuelta','responsable':'DEMO · Andrea Rosales'})
        self.stdout.write(self.style.SUCCESS(
            'EMPRESA DEMO preparada: finca, personal, cuatro cafés, operación, tienda, entregas y QR. Abre /empresa/'))
