"""Datos sintéticos para exhibición; nunca representan producción real."""
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from trazabilidad.models import (Productor, Finca, Lote, ControlCalidad,
    RecepcionCereza, ProcesoCafe, LecturaSensor, MovimientoInventario,
    Pedido, Transporte, EventoTrazabilidad)


class Command(BaseCommand):
    help = 'Crea 20 lotes ficticios y sus operaciones, idempotente y sin eliminar registros existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.localdate()
        now = timezone.now()
        nombres = ['El Mirador', 'La Esperanza', 'San Antonio', 'Los Pinos', 'El Cedro',
                   'Santa Clara', 'La Montaña', 'El Porvenir', 'Las Orquídeas', 'Alto Verde']
        variedades = ['Caturra', 'Bourbon', 'Typica', 'Castillo', 'Geisha']
        estados = ['Aprobado'] * 12 + ['En proceso'] * 5 + ['Rechazado'] * 3
        for i in range(1, 21):
            idx = (i-1) % len(nombres)
            productor, _ = Productor.objects.get_or_create(
                identificacion=f'DEMO-PROD-{idx+1:02d}',
                defaults={'nombre':f'DEMO · Productor {idx+1:02d}',
                          'comunidad':'Datos de ejemplo · Carchi'})
            finca, _ = Finca.objects.get_or_create(
                productor=productor, nombre=f'DEMO · Finca {nombres[idx]}',
                defaults={'canton':'Tulcán', 'provincia':'Carchi',
                          'altura_msnm':1700+idx*75, 'variedad_principal':variedades[idx%5]})
            codigo = f'DEMO-{today.year}-{i:03d}'
            lote = Lote.objects.filter(codigo=codigo).first()
            if lote is None:
                lote = Lote.objects.create(
                    productor=productor, finca=finca, variedad=variedades[i%5],
                    fecha_cosecha=today-timedelta(days=45-i),
                    fecha_ingreso=today-timedelta(days=42-i),
                    cantidad_kg=Decimal(90+i*6),
                    metodo_proceso=['Lavado','Honey','Natural'][i%3],
                    humedad=Decimal('14.2') if i in (4, 11) else Decimal('10.5')+Decimal(i%4)/10,
                    temperatura_secado=Decimal(37+i%7),
                    tiempo_fermentacion_horas=Decimal(18+i%8),
                    estado=estados[i-1],
                    notas='REGISTRO FICTICIO · Solo para demostrar CaféTrace. No es un dato de planta.')
                Lote.objects.filter(pk=lote.pk).update(codigo=codigo)
                lote.codigo=codigo
            base_date=now-timedelta(days=40-i)
            EventoTrazabilidad.objects.get_or_create(
                lote=lote, etapa='Finca', detalle='DEMO · Cosecha ficticia y registro de procedencia',
                defaults={'fecha':base_date, 'ubicacion':finca.nombre, 'responsable':'DEMO · Productor'})
            RecepcionCereza.objects.get_or_create(lote=lote,
                observaciones='DEMO · Recepción simulada',
                defaults={'fecha':base_date+timedelta(days=1), 'peso_kg':lote.cantidad_kg,
                          'humedad_pct':lote.humedad, 'defectos_pct':Decimal(i%4)/10})
            for j, etapa in enumerate(('Beneficio','Fermentación','Secado','Tueste')):
                proc, _ = ProcesoCafe.objects.get_or_create(
                    lote=lote, etapa=etapa, observaciones='DEMO · Proceso simulado',
                    defaults={'inicio':base_date+timedelta(days=j+2),
                              'fin':base_date+timedelta(days=j+2, hours=6),
                              'temperatura_c':Decimal(25+j*10),
                              'humedad_pct':lote.humedad if etapa=='Secado' else Decimal(58-j*8),
                              'ph':Decimal('4.4') if etapa=='Fermentación' else None,
                              'peso_salida_kg':lote.cantidad_kg*Decimal('.82')})
                EventoTrazabilidad.objects.get_or_create(
                    lote=lote, etapa='Secado' if etapa=='Secado' else 'Beneficio',
                    detalle=f'DEMO · {etapa} simulado',
                    defaults={'fecha':base_date+timedelta(days=j+2), 'responsable':'DEMO · Operador'})
                if etapa=='Secado':
                    LecturaSensor.objects.get_or_create(
                        lote=lote, proceso=proc, sensor='DEMO-ESP32', variable='Humedad', origen='Manual',
                        defaults={'instante':base_date+timedelta(days=j+2),
                                  'valor':lote.humedad, 'unidad':'%'})
            if lote.estado != 'En proceso':
                puntaje = Decimal(81+i%10) if lote.estado=='Aprobado' else Decimal(73+i%5)
                ControlCalidad.objects.get_or_create(lote=lote, defaults={
                    'fecha_catacion':today-timedelta(days=14-i%9),
                    'puntaje':puntaje, 'defectos':0 if lote.estado=='Aprobado' else 5,
                    'aroma':'Chocolate, caramelo' if i%2 else 'Cítricos, floral',
                    'sabor':'Dulce, balanceado' if i%2 else 'Frutal, acidez media',
                    'estado':lote.estado,
                    'observaciones':'DEMO · Catación ficticia sin validez técnica'})
            MovimientoInventario.objects.get_or_create(lote=lote, tipo='Entrada',
                referencia='DEMO · Ingreso inicial', defaults={
                    'cantidad_kg':lote.cantidad_kg*Decimal('.78'),
                    'fecha':base_date+timedelta(days=8), 'ubicacion':'DEMO · Bodega UPEC'})
            if i <= 10 and lote.estado=='Aprobado':
                pedido, _ = Pedido.objects.get_or_create(
                    lote=lote, cliente=f'DEMO · Comprador {i:02d}',
                    defaults={'cantidad_kg':Decimal(5+i), 'fecha':now-timedelta(days=8-i%5),
                              'estado':'Entregado' if i<=6 else 'Pendiente',
                              'destino':'DEMO · CEDI UPEC' if i%2==0 else 'DEMO · Tulcán',
                              'destino_cedi':i%2==0, 'codigo_seguimiento':f'DEMO-ENV-{i:03d}'})
                if pedido.estado=='Entregado':
                    MovimientoInventario.objects.get_or_create(lote=lote, tipo='Salida',
                        referencia=f'DEMO · Pedido {pedido.pk}',
                        defaults={'cantidad_kg':pedido.cantidad_kg,
                                  'fecha':now-timedelta(days=3), 'ubicacion':'DEMO · Despacho'})
                Transporte.objects.get_or_create(lote=lote, pedido=pedido,
                    placa=f'DEM-{i:03d}', defaults={
                        'transportista':f'DEMO · Chofer {i}',
                        'origen':'DEMO · Planta UPEC', 'destino':pedido.destino,
                        'fecha_salida':now-timedelta(days=4),
                        'fecha_llegada':now-timedelta(days=3) if i<=6 else None,
                        'temperatura_c':Decimal(20+i%5),
                        'costo_usd':Decimal(12+i),
                        'observaciones':'DEMO · Trayecto ficticio'})
                EventoTrazabilidad.objects.get_or_create(lote=lote, etapa='Transporte',
                    detalle='DEMO · Distribución simulada',
                    defaults={'fecha':now-timedelta(days=3), 'responsable':'DEMO · Transportista'})
        self.stdout.write(self.style.SUCCESS(
            'Datos DEMO cargados: 20 lotes, 10 productores/fincas y registros de calidad, producción, pedidos y transporte.'))
        self.stdout.write('No se borraron datos reales. Repetir el comando no duplica estos registros.')
