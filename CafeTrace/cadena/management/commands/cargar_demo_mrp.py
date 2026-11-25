from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from trazabilidad.models import Lote, EventoTrazabilidad
from cadena.models import Material,MovimientoMaterial,RecetaMaterial,PlanProduccion,PuntoVenta,VentaTienda,Incidencia

class Command(BaseCommand):
    help='Carga datos ficticios repetibles de las cinco áreas y la planificación MRP, sin borrar información previa.'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        call_command('cargar_demo_integral',stdout=self.stdout)
        recursos=[('EMP-250','Bolsa kraft 250 g','unidad','30',3,'100'),
                  ('ETI-QR','Etiqueta de trazabilidad QR','unidad','50',2,'150'),
                  ('CAJA-12','Caja de despacho','unidad','5',4,'20'),
                  ('FIL-CAF','Filtro para café','unidad','10',5,'40')]
        for codigo,nombre,unidad,minimo,plazo,inicio in recursos:
            material,_=Material.objects.get_or_create(codigo=codigo,defaults={
                'nombre':'DEMO · '+nombre,'unidad':unidad,'stock_minimo':Decimal(minimo),
                'plazo_reposicion_dias':plazo,'es_demo':True})
            MovimientoMaterial.objects.get_or_create(material=material,referencia='DEMO-ARRANQUE-'+codigo,
                defaults={'tipo':'Entrada','cantidad':Decimal(inicio),'responsable':'DEMO'})
        for codigo,unidades_por_kg in [('EMP-250','4'),('ETI-QR','4'),('CAJA-12','0.34')]:
            material=Material.objects.get(codigo=codigo)
            RecetaMaterial.objects.get_or_create(nombre='Empaque 250 g',material=material,
                defaults={'cantidad_por_kg':Decimal(unidades_por_kg)})
        lotes=list(Lote.objects.filter(codigo__startswith='DEMO-ESP-').order_by('codigo'))
        for idx,lote in enumerate(lotes[:3]):
            PlanProduccion.objects.get_or_create(lote=lote,receta='Empaque 250 g',
                defaults={'cantidad_objetivo_kg':Decimal('12')+Decimal(idx*4),
                          'responsable':'DEMO · Planificador','es_demo':True})
        puntos=[('DEMO · Cafetería La Montaña','Cafetería','Tulcán'),
                ('DEMO · Tienda de Origen','Tienda','Tulcán'),
                ('DEMO · Mayorista Andino','Mayorista','Quito')]
        for nombre,tipo,ciudad in puntos:
            PuntoVenta.objects.get_or_create(nombre=nombre,defaults={
                'tipo':tipo,'ciudad':ciudad,'direccion':'Dirección ficticia · DEMO','es_demo':True})
        if lotes:
            venta_data=[('DEMO-V-001','DEMO · Cafetería La Montaña',lotes[0],'2.000','18.00'),
                       ('DEMO-V-002','DEMO · Tienda de Origen',lotes[1],'1.000','21.50'),
                       ('DEMO-V-003','DEMO · Mayorista Andino',lotes[2],'8.000','14.00')]
            for numero,punto,lote,cantidad,precio in venta_data:
                VentaTienda.objects.get_or_create(numero=numero,defaults={
                    'punto_venta':PuntoVenta.objects.get(nombre=punto),'lote':lote,
                    'cantidad_kg':Decimal(cantidad),'precio_por_kg':Decimal(precio),'es_demo':True})
            Incidencia.objects.get_or_create(titulo='DEMO · Diferencia de conteo',defaults={
                'area':'Almacén','descripcion':'Ejemplo ficticio de revisión del conteo de empaques.',
                'lote':lotes[0],'responsable':'DEMO · Bodega'})
        self.stdout.write(self.style.SUCCESS('DEMO MRP creado: materiales, recetas, planes, tienda y ventas. Abre / para comenzar.'))
