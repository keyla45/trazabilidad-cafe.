"""Carga datos sintéticos de Café Especial, repetible sin duplicaciones."""
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from trazabilidad.models import VariedadCafe, Lote, EtapaEspecial, PerfilEspecial, PresentacionCafe, Productor, Finca
from trazabilidad.especial_flujos import FLUJOS

class Command(BaseCommand):
    help = 'Crea datos DEMO de los cuatro métodos de café especial sin borrar datos.'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        for nombre in ('Bourbon','Typica','Caturra','Geisha','Castillo','Pacamara'):
            VariedadCafe.objects.get_or_create(nombre=nombre,defaults={'descripcion':'DEMO · Variedad de referencia'})
        prod,_=Productor.objects.get_or_create(identificacion='DEMO-ESP-PROD',defaults={'nombre':'DEMO · Productor café especial'})
        finca,_=Finca.objects.get_or_create(productor=prod,nombre='DEMO · Finca La Esperanza',defaults={'provincia':'Carchi','canton':'Tulcán','altura_msnm':1920})
        for i,(metodo,etapas) in enumerate(FLUJOS.items(),start=1):
            codigo=f'DEMO-ESP-{i:02d}'
            lote=Lote.objects.filter(codigo=codigo).first()
            if lote is None:
                lote=Lote.objects.create(productor=prod,finca=finca,variedad=['Bourbon','Caturra','Geisha','Typica'][i-1],fecha_cosecha=timezone.localdate()-timedelta(days=35),cantidad_kg=Decimal('120.00'),metodo_proceso=metodo,humedad=Decimal('11.2'),notas='DEMO · Valores ficticios, no son datos experimentales.')
                Lote.objects.filter(pk=lote.pk).update(codigo=codigo);lote.codigo=codigo
            elif lote.metodo_proceso!=metodo:
                self.stdout.write(f'Omitido {codigo}: proceso cambiado manualmente');continue
            base=timezone.now()-timedelta(days=30)
            for n,nombre in enumerate(etapas,start=1):
                EtapaEspecial.objects.get_or_create(lote=lote,orden=n,defaults={'nombre':nombre,'estado':'Finalizada' if n<=5 else 'Pendiente','responsable':'DEMO · Operador','fecha_inicio':base+timedelta(days=n),'fecha_fin':base+timedelta(days=n,hours=4) if n<=5 else None,'temperatura_c':Decimal('28.5') if 'Fermentación' in nombre else None,'humedad_pct':Decimal('11.2') if 'Secado' in nombre else None,'observaciones':'DEMO · Etapa ilustrativa'})
            if i!=4:
                PerfilEspecial.objects.get_or_create(lote=lote,defaults={'variedad_catalogo':VariedadCafe.objects.filter(nombre=lote.variedad).first(),'catador':'DEMO · Evaluador','puntaje_total':Decimal(83+i),'aroma':Decimal('8.00'),'sabor':Decimal('8.25'),'acidez':Decimal('7.75'),'cuerpo':Decimal('8.00'),'balance':Decimal('8.00'),'notas_sensoriales':'DEMO · Chocolate, fruta madura, caramelo','decision':'Pendiente','observaciones':'Dato ficticio; puntaje informado, no cálculo SCA.'})
            for peso in (250,500,1000):
                PresentacionCafe.objects.get_or_create(codigo_sku=f'DEMO-ESP-{i:02d}-{peso}',defaults={'lote':lote,'nombre':f'Café {metodo} {peso} g','formato':'Grano','gramos_por_unidad':peso,'unidades':20,'precio_usd':Decimal('8.50')*(Decimal(peso)/Decimal(250)),'es_demo':True})
        self.stdout.write(self.style.SUCCESS('DEMO Café Especial: 4 métodos, flujos por lote, perfiles y 12 presentaciones disponibles.'))
