"""Datos ficticios repetibles para recorrido completo de café especial."""
from datetime import timedelta
from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from trazabilidad.especial_flujos import FLUJOS
from trazabilidad.models import (Lote, EtapaEspecial, PerfilEspecial, EventoTrazabilidad,
    RecepcionCereza, ProcesoCafe, LecturaSensor, MovimientoInventario, Pedido, Transporte, ControlCalidad)

class Command(BaseCommand):
    help = "Crea un recorrido ficticio completo: finca, recepción, procesos, sensores, calidad, almacén, pedido, transporte, QR."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        call_command('cargar_demo_especial', stdout=self.stdout)
        now=timezone.now()
        for i in range(1,5):
            lote=Lote.objects.get(codigo=f'DEMO-ESP-{i:02d}')
            t0=now-timedelta(days=24-i)
            descripcion='DEMO · Datos simulados para aprender a usar CaféTrace, no mediciones de la UPEC.'
            RecepcionCereza.objects.get_or_create(lote=lote, observaciones=descripcion,defaults={
                'fecha':t0,'peso_kg':Decimal('120.00'),'humedad_pct':Decimal('12.00'),'defectos_pct':Decimal('1.20')})
            etapas=list(lote.etapas_especiales.order_by('orden'))
            for n,etapa in enumerate(etapas,1):
                EtapaEspecial.objects.filter(pk=etapa.pk).update(
                    estado='Finalizada' if n<=max(1,len(etapas)-2) else 'En curso' if n==len(etapas)-1 else 'Pendiente',
                    responsable='DEMO · Operador de beneficio',ubicacion='DEMO · Planta de café',
                    fecha_inicio=t0+timedelta(hours=n*6),
                    fecha_fin=t0+timedelta(hours=n*6+3) if n<=len(etapas)-2 else None,
                    peso_entrada_kg=Decimal('120.00')-Decimal(n-1)*Decimal('4.00'),
                    peso_salida_kg=Decimal('120.00')-Decimal(n)*Decimal('4.00') if n<=len(etapas)-2 else None,
                    observaciones=descripcion)
                if n<=len(etapas)-2:
                    EventoTrazabilidad.objects.get_or_create(lote=lote,etapa='Beneficio',detalle=f'DEMO · {etapa.nombre}',defaults={
                        'fecha':t0+timedelta(hours=n*6+3),'ubicacion':'DEMO · Planta de café','responsable':'DEMO · Operador'})
            for etapa_nombre in ('Fermentación','Secado','Tueste'):
                proc,_=ProcesoCafe.objects.get_or_create(lote=lote,etapa=etapa_nombre,observaciones=descripcion,defaults={
                    'inicio':t0+timedelta(days=1),'fin':t0+timedelta(days=2),
                    'temperatura_c':Decimal('27.40') if etapa_nombre!='Tueste' else Decimal('190.00'),
                    'humedad_pct':Decimal('11.10') if etapa_nombre=='Secado' else None,
                    'ph':Decimal('4.40') if etapa_nombre=='Fermentación' else None,
                    'peso_salida_kg':Decimal('80.00')})
                variable='Humedad' if etapa_nombre=='Secado' else 'Temperatura'
                unidad='%' if variable=='Humedad' else '°C'
                valor=Decimal('11.10') if variable=='Humedad' else Decimal('190.00') if etapa_nombre=='Tueste' else Decimal('27.40')
                LecturaSensor.objects.get_or_create(lote=lote,proceso=proc,sensor=f'DEMO-{etapa_nombre}',variable=variable,origen='Manual',defaults={
                    'instante':t0+timedelta(days=2),'valor':valor,'unidad':unidad})
            EventoTrazabilidad.objects.get_or_create(lote=lote,etapa='Finca',detalle='DEMO · Cosecha en finca ficticia',defaults={
                'fecha':t0-timedelta(days=2),'ubicacion':lote.finca.nombre,'responsable':lote.productor.nombre})
            EventoTrazabilidad.objects.get_or_create(lote=lote,etapa='Recepción',detalle='DEMO · Recepción, pesaje e inspección',defaults={
                'fecha':t0,'ubicacion':'DEMO · Planta','responsable':'DEMO · Acopiador'})
            if i<=3:
                PerfilEspecial.objects.filter(lote=lote).update(decision='Aprobado')
                ControlCalidad.objects.update_or_create(lote=lote,defaults={
                    'fecha_catacion':timezone.localdate()-timedelta(days=3), 'puntaje':Decimal('85.00')+i,
                    'defectos':0,'aroma':'DEMO · Floral y dulce','sabor':'DEMO · Chocolate y fruta',
                    'estado':'Aprobado','observaciones':descripcion})
                Lote.objects.filter(pk=lote.pk).update(estado='Aprobado')
            MovimientoInventario.objects.get_or_create(lote=lote,tipo='Entrada',referencia=f'DEMO-ING-{i}',defaults={
                'fecha':t0+timedelta(days=5),'cantidad_kg':Decimal('50.00'),'ubicacion':'DEMO · Bodega A'})
            if i<=2:
                pedido,_=Pedido.objects.get_or_create(lote=lote,codigo_seguimiento=f'DEMO-ENV-{i:02d}',defaults={
                    'cliente':'DEMO · Cafetería La Montaña' if i==1 else 'DEMO · Mayorista Andino',
                    'contacto':'Contacto ficticio','cantidad_kg':Decimal('5.00'), 'fecha':now-timedelta(days=2),
                    'estado':'Entregado','destino':'DEMO · Tulcán', 'destino_cedi':i==2})
                MovimientoInventario.objects.get_or_create(lote=lote,tipo='Salida',referencia=f'DEMO-ENV-{i:02d}',defaults={
                    'fecha':now-timedelta(days=2),'cantidad_kg':Decimal('5.00'),'ubicacion':'DEMO · Bodega A'})
                Transporte.objects.get_or_create(lote=lote,pedido=pedido,placa=f'DEMO-{i:03d}',defaults={
                    'transportista':'DEMO · Transportista','origen':'DEMO · Planta','destino':pedido.destino,
                    'fecha_salida':now-timedelta(days=2),'fecha_llegada':now-timedelta(days=1),
                    'temperatura_c':Decimal('21.00'),'costo_usd':Decimal('8.00'),'observaciones':descripcion})
                for etapa,detalle in [('Almacenamiento','Ingreso DEMO a bodega'),('Transporte','Despacho DEMO al cliente'),('Venta','Entrega DEMO realizada')]:
                    EventoTrazabilidad.objects.get_or_create(lote=lote,etapa=etapa,detalle=detalle,defaults={
                        'fecha':now-timedelta(days=1),'ubicacion':'DEMO · Tulcán','responsable':'DEMO · Logística'})
        self.stdout.write(self.style.SUCCESS('DEMO integral listo: 4 lotes, etapas, recepciones, sensores, calidad, inventario y 2 entregas. Abrir /demo/'))
