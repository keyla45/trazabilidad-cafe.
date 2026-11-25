"""Escenario ficticio multimarcas para demostrar catálogo, gramajes y trazabilidad.
Seguro para reejecución; no elimina ni sobrescribe registros reales.
"""
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from trazabilidad.models import Productor, Finca, Lote, EventoTrazabilidad, EtapaEspecial
from cadena.models import MarcaCafe, ProductoCatalogo, PuntoVenta

CAFES = [
 ('Geisha','Arábica','Lavado',0,11.50),
 ('Bourbon','Arábica','Honey',1,9.20),
 ('Caturra','Arábica','Natural',2,8.80),
 ('Typica','Arábica','Anaeróbico',3,12.40),
 ('Robusta','Robusta','Natural',1,6.70),
 ('Conilon','Robusta','Lavado',2,7.10),
 ('Liberica','Libérica','Honey',3,10.10),
 ('Excelsa','Excelsa','Natural',0,10.80),
]
FINCAS = [
 ('DEMO · Finca La Esperanza','Tulcán','Carchi',1900,'Juan Pérez'),
 ('DEMO · Finca Río Verde','Loja','Loja',1550,'María Paredes'),
 ('DEMO · Finca Amanecer','Ibarra','Imbabura',1350,'Pedro Molina'),
 ('DEMO · Finca Bosque Alto','Zamora','Zamora Chinchipe',1250,'Diana Ruiz'),
]
MARCAS = [
 ('DEMO · Origen y Taza','La historia comienza en la finca.'),
 ('DEMO · Cumbre Andina','Sabores de altura, historias de origen.'),
 ('DEMO · Raíces del Café','Del cultivo a una taza con identidad.'),
 ('DEMO · Montaña Dorada','Cada lote tiene una historia.'),
 ('DEMO · Aroma del Valle','Un recorrido de sabores y procesos.'),
 ('DEMO · Terruño Café','Conoce la procedencia de tu café.'),
]
ETAPAS = {
 'Lavado':['Cosecha','Recepción','Selección','Despulpado','Fermentación','Lavado','Secado','Trilla','Tostión','Empaque','Bodega','Despacho a tienda'],
 'Natural':['Cosecha','Recepción','Selección','Secado en cereza','Trilla','Clasificación','Tostión','Empaque','Bodega','Despacho a tienda'],
 'Honey':['Cosecha','Recepción','Selección','Despulpado','Secado con mucílago','Trilla','Clasificación','Tostión','Empaque','Bodega','Despacho a tienda'],
 'Anaeróbico':['Cosecha','Recepción','Selección','Fermentación anaeróbica','Lavado según proceso','Secado','Trilla','Clasificación','Tostión','Empaque','Bodega','Despacho a tienda'],
}

class Command(BaseCommand):
    help = 'Carga 8 cafés, 6 marcas, 48 presentaciones y fichas de proceso DEMO. Idempotente.'

    @transaction.atomic
    def handle(self,*args,**kwargs):
        marcas=[]
        for nombre,lema in MARCAS:
            marca,_=MarcaCafe.objects.get_or_create(nombre=nombre,defaults={'lema':lema,'descripcion':'Marca ficticia para la práctica académica.','es_demo':True,'activa':True})
            marcas.append(marca)
        fincas=[]
        for i,(nombre,ciudad,provincia,altura,persona) in enumerate(FINCAS):
            productor,_=Productor.objects.get_or_create(identificacion=f'DEMO-MAR-PROD-{i+1:02d}',defaults={'nombre':'DEMO · '+persona,'comunidad':'Productor ficticio del escenario académico'})
            finca,_=Finca.objects.get_or_create(productor=productor,nombre=nombre,defaults={'canton':ciudad,'provincia':provincia,'altura_msnm':altura,'parroquia':'Parcela simulada'})
            fincas.append(finca)
        inicio=timezone.now()-timedelta(days=35)
        for i,(variedad,especie,metodo,finca_idx,base) in enumerate(CAFES):
            finca=fincas[finca_idx]
            cosecha=timezone.localdate()-timedelta(days=35-i)
            lote,_=Lote.objects.get_or_create(codigo=f'DEMO-MAR-{i+1:02d}',defaults={'productor':finca.productor,'finca':finca,'variedad':variedad,
                'fecha_cosecha':cosecha,'fecha_ingreso':cosecha,'metodo_proceso':metodo,'cantidad_kg':Decimal('80.00'),
                'estado':'Aprobado','notas':'FICTICIO DEMO · Datos del proceso creados únicamente para mostrar la trazabilidad.'})
            for j,nombre in enumerate(ETAPAS[metodo],1):
                cuando=inicio+timedelta(days=i+j)
                # Los procesos son una simulación, no mediciones de laboratorio.
                EtapaEspecial.objects.get_or_create(lote=lote,orden=j,defaults={'nombre':nombre,'fecha_inicio':cuando,
                    'fecha_fin':cuando+timedelta(hours=3),'responsable':'DEMO · Equipo Origen y Taza',
                    'ubicacion':finca.nombre if j<6 else 'DEMO · Planta y tienda Origen y Taza',
                    'estado':'Finalizada','observaciones':'Proceso ilustrativo registrado para mostrar el recorrido; no es una operación real.'})
            for j,(etapa,detalle) in enumerate([('Finca','Café cosechado en origen simulado.'),('Recepción','Materia prima identificada por lote.'),('Beneficio','Método '+metodo+' registrado.'),('Secado','Secado del producto en escenario DEMO.'),('Almacenamiento','Ingreso a bodega ficticia.'),('Transporte','Despacho ficticio a punto de venta.'),('Venta','Exhibido en tienda DEMO, no equivale a venta efectiva.')],1):
                EventoTrazabilidad.objects.get_or_create(lote=lote,etapa=etapa,detalle='DEMO · '+detalle,defaults={'fecha':inicio+timedelta(days=i+j+3),'ubicacion':'Escenario ficticio · Origen y Taza','responsable':'DEMO · Equipo de operaciones'})
            # Dos marcas por café y tres gramajes: el precio depende del peso y la marca.
            for j,marca in enumerate((marcas[i%len(marcas)],marcas[(i+2)%len(marcas)])):
                for gramos,mult in [(250,Decimal('1.00')),(500,Decimal('1.87')),(1000,Decimal('3.56'))]:
                    precio=(Decimal(str(base))*mult+(Decimal('0.80') if j else Decimal('0.00'))).quantize(Decimal('0.01'))
                    formato='Grano' if j==0 else 'Molido'
                    sku=f'DEMO-{i+1:02d}-{j+1:01d}-{gramos}'
                    ProductoCatalogo.objects.get_or_create(sku=sku,defaults={'marca':marca,'lote':lote,'titulo':variedad+' '+metodo,
                        'especie':especie,'categoria':'Café de origen (DEMO)' if especie!='Arábica' else 'Café de especialidad (DEMO)',
                        'formato':formato,'gramos':gramos,'precio_usd':precio,'unidades':24+i*3+j*4,
                        'descripcion':f'Presentación de {gramos} g con proceso {metodo}. Marca y precio de demostración; consulte el historial trazable del lote.',
                        'activo':True,'es_demo':True})
        PuntoVenta.objects.get_or_create(nombre='DEMO · Tienda Origen y Taza',defaults={'tipo':'Tienda','ciudad':'Tulcán','direccion':'Local ficticio, sin dirección real','es_demo':True})
        self.stdout.write(self.style.SUCCESS('CATÁLOGO DEMO: 8 tipos, 6 marcas, 48 SKU con gramajes, precios, finca, procesos y QR. Abre /explorar/'))
