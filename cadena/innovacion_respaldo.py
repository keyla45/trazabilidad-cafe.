"""Herramientas demostrables: analítica, guía, API de solo lectura y chatbot basado en reglas.
Sin IA externa ni claves de terceros: las respuestas se apoyan en registros locales.
"""
from collections import Counter
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from trazabilidad.models import Lote, Productor, RecepcionCereza, ProcesoCafe, Pedido, MovimientoInventario, EventoTrazabilidad
from .models import Material, PuntoVenta, VentaTienda, Incidencia, PlanProduccion


def _autorizado(user):
    """Las métricas de negocio no se comparten con clientes finales."""
    return user.is_superuser or user.is_staff or user.groups.exclude(name='Cliente').exists()


def _metrics():
    estados = list(Lote.objects.values_list('estado', flat=True))
    procesos = list(Lote.objects.values_list('metodo_proceso', flat=True))
    ingresos = MovimientoInventario.objects.filter(tipo='Entrada').aggregate(v=Sum('cantidad_kg'))['v'] or Decimal('0')
    salidas = MovimientoInventario.objects.filter(tipo='Salida').aggregate(v=Sum('cantidad_kg'))['v'] or Decimal('0')
    return {
        'lotes':Lote.objects.count(), 'productores':Productor.objects.count(),
        'recepciones':RecepcionCereza.objects.count(), 'procesos':ProcesoCafe.objects.count(),
        'materiales':Material.objects.count(), 'planes_mrp':PlanProduccion.objects.count(),
        'puntos_venta':PuntoVenta.objects.count(), 'ventas':VentaTienda.objects.count(),
        'pedidos':Pedido.objects.count(), 'pedidos_pendientes':Pedido.objects.filter(estado='Pendiente').count(),
        'incidencias_abiertas':Incidencia.objects.filter(estado='Abierta').count(),
        'stock_lotes_kg':float(ingresos - salidas),
        'por_estado':dict(Counter(estados)), 'por_metodo':dict(Counter(procesos)),
    }


def _links():
    return [
        ('Agricultor y proveedor',reverse('cadena_area',args=['proveedor'])),
        ('Producción y MRP',reverse('cadena_area',args=['produccion'])),
        ('Almacén',reverse('cadena_area',args=['almacen'])),
        ('Distribución',reverse('cadena_area',args=['distribucion'])),
        ('Clientes y tienda',reverse('cadena_area',args=['tienda'])),
        ('Catálogo',reverse('cadena_catalogo')),
        ('Códigos QR',reverse('cadena_qrs')),
        ('Experimentos E1-E3',reverse('cadena_experimentos')),
    ]


@login_required
def centro(request):
    if not _autorizado(request.user):return HttpResponseForbidden('Área exclusiva para personal autorizado.')
    return render(request,'cadena/innovacion.html',{
        'm':_metrics(), 'enlaces':_links(),
        'lotes_recientes':Lote.objects.select_related('finca').order_by('-id')[:6],
        'pedidos_recientes':Pedido.objects.select_related('lote').order_by('-fecha')[:5],
        'demo': True,
    })


@login_required
@require_GET
def api_resumen(request):
    """API JSON autenticada, de sólo lectura, sin datos privados."""
    if not _autorizado(request.user):return JsonResponse({'error':'Sin autorización'},status=403)
    return JsonResponse({'version':'1.0','origen':'CafeTrace Django','tipo':'consulta','metricas':_metrics()})


@login_required
@require_GET
def api_trazabilidad(request,codigo):
    if not _autorizado(request.user):return JsonResponse({'error':'Sin autorización'},status=403)
    lote=Lote.objects.filter(codigo=codigo).select_related('finca').first()
    if not lote:
        return JsonResponse({'error':'Lote no encontrado'},status=404)
    eventos=list(EventoTrazabilidad.objects.filter(lote=lote).order_by('fecha').values('etapa','fecha','ubicacion','detalle'))
    procesos=list(ProcesoCafe.objects.filter(lote=lote).order_by('inicio').values('etapa','inicio','fin'))
    return JsonResponse({'codigo':lote.codigo,'variedad':lote.variedad,
        'metodo':lote.metodo_proceso,'estado':lote.estado,
        'origen':lote.finca.nombre,'eventos':eventos,'procesos':procesos},json_dumps_params={'ensure_ascii':False})


@login_required
@require_GET
def asistente(request):
    """Asistente guiado de reglas; no se presenta como LLM generativo."""
    if not _autorizado(request.user):return JsonResponse({'error':'Sin autorización'},status=403)
    q=request.GET.get('q','').strip()[:240]
    if not q:
        return JsonResponse({'respuesta':'Puedes preguntarme por lotes, inventario, ventas, distribución, QR o MRP.', 'url':reverse('cadena_catalogo'),'etiqueta':'Explorar cafés'})
    s=q.casefold()
    m=_metrics()
    if any(w in s for w in ['qr','trazabilidad','origen','historia']):
        r=f'Hay {m["lotes"]} lotes registrados. Desde QR puedes abrir el recorrido publicado de cada lote. Las etapas solo se muestran si fueron registradas.'
        url=reverse('cadena_qrs'); e='Consultar QR'
    elif any(w in s for w in ['mrp','requerim','insumo','material','planific']):
        r=f'Hay {m["materiales"]} materiales y {m["planes_mrp"]} planes de producción. El MRP calcula necesidades a partir de recetas y existencias.'
        url=reverse('cadena_mrp'); e='Abrir MRP'
    elif any(w in s for w in ['pedido','despacho','entrega','transporte','distrib']):
        r=f'Existen {m["pedidos"]} pedidos registrados, de los cuales {m["pedidos_pendientes"]} están pendientes. Abre Distribución para consultar sus estados.'
        url=reverse('cadena_area',args=['distribucion']); e='Ir a Distribución'
    elif any(w in s for w in ['venta','cliente','tienda','precio','compr']) and not any(w in s for w in ['inventario','stock','kardex','existenc','almac']):
        r=f'Existen {m["puntos_venta"]} puntos de venta y {m["ventas"]} ventas registradas. Los registros DEMO son ficticios.'
        url=reverse('cadena_area',args=['tienda']); e='Ir a Tienda'
    elif any(w in s for w in ['almac','stock','inventario','kardex','existenc']):
        r=f'El saldo registrado de movimientos de café es {m["stock_lotes_kg"]:.2f} kg. Es un saldo contable, no un conteo físico verificado.'
        url=reverse('cadena_area',args=['almacen']); e='Ver almacén'
    elif any(w in s for w in ['producc','tueste','beneficio','secado','proces']):
        r=f'Hay {m["procesos"]} procesos registrados. Para ver etapas por lote, abre Producción o el catálogo.'
        url=reverse('cadena_area',args=['produccion']); e='Ir a Producción'
    elif any(w in s for w in ['proveedor','agricult','finca','cosecha']):
        r=f'Hay {m["productores"]} productores y {m["recepciones"]} recepciones documentadas.'
        url=reverse('cadena_area',args=['proveedor']); e='Ir a Origen'
    else:
        r='Puedo orientarte sobre los cinco módulos, MRP, inventario, pedidos y QR. Para una consulta más precisa, menciona uno de esos temas. No invento datos ni emito certificaciones.'
        url=reverse('cadena_catalogo'); e='Explorar catálogo'
    return JsonResponse({'respuesta':r,'url':url,'etiqueta':e},json_dumps_params={'ensure_ascii':False})
