"""Interfaz de monitoreo y exportación verificable para el capítulo 6."""
import csv
import json
import os
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Lote, LecturaSensor, ProcesoCafe, Pedido, Transporte, MovimientoInventario, EvaluacionExperimental, PerfilEspecial, EventoTrazabilidad
from .permissions import role_required

@role_required('Bodega','Producción','Almacén','Control de calidad')
def laboratorio(request):
    origen=request.GET.get('origen','todos')
    lotes=Lote.objects.select_related('finca','productor')
    if origen=='demo': lotes=lotes.filter(Q(codigo__startswith='DEMO-')|Q(notas__icontains='DEMO'))
    elif origen=='real': lotes=lotes.exclude(Q(codigo__startswith='DEMO-')|Q(notas__icontains='DEMO'))
    lote_ids=list(lotes.values_list('id',flat=True))
    lecturas=LecturaSensor.objects.select_related('lote','proceso').filter(lote_id__in=lote_ids).order_by('-instante')[:50]
    experimentos={k:EvaluacionExperimental.objects.filter(experimento=k).order_by('-fecha')[:10] for k in ['E1','E2','E3']}
    inventario=MovimientoInventario.objects.filter(lote_id__in=lote_ids).aggregate(entrada=Sum('cantidad_kg',filter=Q(tipo='Entrada')),salida=Sum('cantidad_kg',filter=Q(tipo='Salida')))
    stock=(inventario['entrada'] or Decimal('0'))-(inventario['salida'] or Decimal('0'))
    procesos=ProcesoCafe.objects.filter(lote_id__in=lote_ids)
    ctx={'origen':origen,'lotes_count':len(lote_ids),'lecturas_count':LecturaSensor.objects.filter(lote_id__in=lote_ids).count(),
         'procesos_count':procesos.count(),'stock':stock,'pedidos_count':Pedido.objects.filter(lote_id__in=lote_ids).count(),
         'transportes_count':Transporte.objects.filter(lote_id__in=lote_ids).count(),
         'lecturas':lecturas,'experimentos':experimentos,'promedio_humedad':LecturaSensor.objects.filter(lote_id__in=lote_ids,variable='Humedad').aggregate(n=Avg('valor'))['n'],
         'alertas_humedad':Lote.objects.filter(id__in=lote_ids,humedad__gt=Decimal('12')).count(),
         'pedidos':Pedido.objects.filter(lote_id__in=lote_ids).select_related('lote').order_by('-fecha')[:12],
         'envios':Transporte.objects.filter(lote_id__in=lote_ids).select_related('lote').order_by('-fecha_salida')[:12],
         'lotes':lotes[:30], 'sensor_configurado':bool(os.getenv('CAFETRACE_SENSOR_TOKEN'))}
    return render(request,'integracion/laboratorio.html',ctx)

@role_required('Bodega','Producción','Almacén','Control de calidad')
def exportar_lecturas(request):
    r=HttpResponse(content_type='text/csv; charset=utf-8')
    r['Content-Disposition']='attachment; filename="cafetrace_lecturas_capitulo6.csv"'
    r.write('\ufeff')
    w=csv.writer(r)
    w.writerow(['lote','instante','etapa','sensor','variable','valor','unidad','origen','tipo_registro'])
    for x in LecturaSensor.objects.select_related('lote','proceso').order_by('instante').iterator():
        demo=x.lote.codigo.startswith('DEMO-') or 'DEMO' in (x.lote.notas or '').upper()
        w.writerow([x.lote.codigo,x.instante.isoformat(),x.proceso.etapa if x.proceso_id else '',x.sensor,x.variable,x.valor,x.unidad,x.origen,'DEMO' if demo else 'OPERATIVO'])
    return r

@csrf_exempt
@require_POST
def ingresar_sensor(request):
    """Ingesta opcional ESP32/Node-RED. HTTPS y token por cabecera X-CafeTrace-Token."""
    import hmac
    token=os.getenv('CAFETRACE_SENSOR_TOKEN','')
    if not token: return JsonResponse({'error':'La integración IoT no está configurada'},status=503)
    if not hmac.compare_digest(request.headers.get('X-CafeTrace-Token',''),token): return JsonResponse({'error':'No autorizado'},status=403)
    if len(request.body)>4096: return JsonResponse({'error':'Solicitud demasiado grande'},status=413)
    try:
        d=json.loads(request.body)
        lote=Lote.objects.get(codigo=d['lote'])
        variable=d['variable']; unidad=d['unidad']; valor=Decimal(str(d['valor']))
        unidades={'Humedad':'%','Temperatura':'°C','pH':'pH'}
        rangos={'Humedad':(0,100),'Temperatura':(-30,300),'pH':(0,14)}
        if variable not in unidades or unidad!=unidades[variable] or not valor.is_finite() or not rangos[variable][0] <= valor <= rangos[variable][1]:
            return JsonResponse({'error':'Variable, unidad o valor no válido'},status=400)
        sensor=str(d['sensor']).strip()[:100]
        if not sensor:return JsonResponse({'error':'Sensor obligatorio'},status=400)
        proceso=None
        if d.get('proceso_id'):
            proceso=ProcesoCafe.objects.get(pk=d['proceso_id'],lote=lote)
        x=LecturaSensor.objects.create(lote=lote,proceso=proceso,sensor=sensor,variable=variable,unidad=unidad,valor=valor,origen='IoT')
        return JsonResponse({'ok':True,'id':x.pk,'instante':x.instante.isoformat()},status=201)
    except (ValueError,KeyError,TypeError,InvalidOperation,json.JSONDecodeError, Lote.DoesNotExist, ProcesoCafe.DoesNotExist):
        return JsonResponse({'error':'Solicitud inválida o lote/proceso inexistente'},status=400)
