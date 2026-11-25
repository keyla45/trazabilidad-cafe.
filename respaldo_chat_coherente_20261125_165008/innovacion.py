"""Herramientas demostrables: analítica, guía, API de solo lectura y chatbot basado en reglas.
Sin IA externa ni claves de terceros: las respuestas se apoyan en registros locales.
"""
from collections import Counter
import re
import unicodedata
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from trazabilidad.models import Lote, Productor, RecepcionCereza, ProcesoCafe, Pedido, MovimientoInventario, EventoTrazabilidad
from .models import Material, MovimientoMaterial, PuntoVenta, VentaTienda, Incidencia, PlanProduccion


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
        'guias': [{**g, 'url':reverse(g['url_nombre'],args=g['url_args'])} for g in GUIAS],
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


# Guías informativas; no ejecutan acciones ni se confunden con agentes autónomos.
GUIAS = [
    {'clave':'proveedor','titulo':'1 · Agricultor y proveedor','descripcion':'Registrar productor, finca, cosecha y recepción. Revisar peso y procedencia.', 'url_nombre':'cadena_area','url_args':['proveedor']},
    {'clave':'produccion','titulo':'2 · Producción y MRP','descripcion':'Verificar beneficio, trilla, tueste, empaque e insumos para el plan.', 'url_nombre':'cadena_area','url_args':['produccion']},
    {'clave':'almacen','titulo':'3 · Almacén e inventario','descripcion':'Comprobar entradas, salidas, saldos y materiales antes de despachar.', 'url_nombre':'cadena_area','url_args':['almacen']},
    {'clave':'distribucion','titulo':'4 · Distribución','descripcion':'Revisar pedido, preparación, despacho, transporte y entrega.', 'url_nombre':'cadena_area','url_args':['distribucion']},
    {'clave':'tienda','titulo':'5 · Clientes y tienda','descripcion':'Consultar presentaciones, precios, punto de venta y QR del lote.', 'url_nombre':'cadena_area','url_args':['tienda']},
]


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD',texto.casefold()) if not unicodedata.combining(c))


def _contiene(texto, palabras):
    # Palabras completas: "venta" NO coincide con "inventario".
    return any(re.search(r'(?<!\w)'+re.escape(p)+r'\w*(?!\w)', texto) for p in palabras)


def _lote_solicitado(q):
    # Evita consultas por coincidencia parcial que revelen datos de otro lote.
    codigos = re.findall(r'\b(?:DEMO[-_]?ESP[-_]?\d+|CAF[-_]?\d{4}[-_A-Z0-9]+)\b', q, flags=re.I)
    if codigos:
        return Lote.objects.filter(codigo__iexact=codigos[0]).select_related('finca','productor').first(), codigos[0]
    return None, None


def _respuesta_lote(lote):
    eventos=list(lote.eventos.order_by('fecha').values_list('etapa',flat=True)[:14])
    procesos=list(lote.procesos.order_by('inicio').values_list('etapa',flat=True)[:12])
    mov=lote.movimientos.values('tipo').annotate(total=Sum('cantidad_kg'))
    cantidades={e['tipo']:e['total'] for e in mov}
    saldo=(cantidades.get('Entrada') or Decimal('0'))-(cantidades.get('Salida') or Decimal('0'))
    etapas=', '.join(dict.fromkeys(eventos+procesos)) or 'No hay etapas registradas'
    texto=(f'Lote {lote.codigo}: {lote.variedad}, método {lote.metodo_proceso}, estado {lote.estado}. '
           f'Origen registrado: {lote.finca.nombre}. Productor: {lote.productor.nombre}. '
           f'Etapas registradas: {etapas}. Saldo documental: {saldo:.2f} kg. '
           'El saldo no sustituye un conteo físico. Consulta su ficha para comprobar fechas y responsables.')
    return texto, reverse('detalle_lote', args=[lote.id]), 'Abrir historial del lote'


@login_required
@require_GET
def asistente(request):
    """Asistente contextual de solo lectura con datos reales de la BD y guía por área.

    No es un LLM. No publica datos personales mediante la API pública.
    """
    if not _autorizado(request.user):
        return JsonResponse({'error':'Sin autorización'},status=403)
    q=request.GET.get('q','').strip()[:240]
    sugerencias=[
      '¿Qué puedo hacer en cada área?', '¿Cuánto stock de café tenemos?',
      '¿Cuántos pedidos están pendientes?', '¿Cómo consulto un QR?',
      '¿Qué materiales necesita producción?',
    ]
    if not q:
        return JsonResponse({'respuesta':'Soy el asistente operativo de CaféTrace. Puedo consultar datos registrados y guiarte paso a paso. No ejecuto cambios ni invento resultados.',
          'url':reverse('cadena_empresa_demo') if request.user.is_superuser else reverse('cadena_catalogo'),
          'etiqueta':'Abrir empresa DEMO' if request.user.is_superuser else 'Explorar cafés',
          'sugerencias':sugerencias,'fuente':'Base local de CaféTrace'})
    s=_normalizar(q)
    lote, codigo=_lote_solicitado(q)
    if codigo and not lote:
        return JsonResponse({'respuesta':f'No encontré el lote {codigo}. Revisa el código exacto en Lotes o en la empresa DEMO.',
          'url':reverse('lista_lotes'),'etiqueta':'Buscar lotes','sugerencias':['¿Cómo consulto un QR?'], 'fuente':'Consulta de lotes'})
    if lote:
        r,url,e=_respuesta_lote(lote)
        return JsonResponse({'respuesta':r,'url':url,'etiqueta':e,
          'sugerencias':['¿Cómo consulto un QR?','¿Cuánto stock de café tenemos?'], 'fuente':f'Lote {lote.codigo} · base de datos'})

    # La intención de la pregunta prevalece sobre una palabra del módulo.
    # Por ejemplo, «¿para qué sirve almacén?» no es una solicitud del saldo.
    pregunta_explicativa = _contiene(s, ['para que', 'que hace', 'que funcion', 'para que se usa',
                                        'como funciona', 'como se usa', 'en que consiste',
                                        'explicame', 'explica', 'cual es la funcion'])
    if pregunta_explicativa:
        conceptos = [
            (['almacen','bodega','inventario','kardex'],
             'El módulo de Almacén controla el café y los materiales que entran, se almacenan y salen de la empresa. '
             'Sirve para registrar movimientos por lote, comprobar el saldo documental y consultar el Kardex. '
             'Ejemplo: se reciben 80 kg de café tostado, se registra la entrada y, al preparar un pedido de 12 kg, '
             'se registra su salida. Así queda documentado qué lote se movió, cuándo y cuánto. '
             'El saldo del sistema debe contrastarse con un conteo físico.',
             reverse('cadena_area',args=['almacen']), 'Abrir módulo Almacén'),
            (['proveedor','agricultor','finca','cosecha','recepcion','productor'],
             'El módulo de Agricultor y proveedor identifica quién cultivó el café, la finca de procedencia, '
             'la cosecha y su recepción. Sirve para crear el lote trazable y documentar cantidades, fechas y '
             'beneficio inicial. Ejemplo: registrar el ingreso de café cereza con el código de lote antes de '
             'enviarlo a secado o transformación.',
             reverse('cadena_area',args=['proveedor']), 'Abrir Agricultor y proveedor'),
            (['produccion','tueste','tostion','secado','empaque','beneficio','transformacion'],
             'El módulo de Producción y logística documenta las transformaciones del lote: beneficio, '
             'secado, trilla, tostión y empaque, según correspondan. También permite planificar materiales '
             'mediante MRP. Ejemplo: seleccionar un lote, registrar la cantidad de entrada, la operación, '
             'el responsable y la salida obtenida; así se conserva la trazabilidad y el rendimiento.',
             reverse('cadena_area',args=['produccion']), 'Abrir Producción'),
            (['mrp','planificacion','requerimiento','receta','insumo'],
             'MRP significa planificación de requerimientos de materiales. Sirve para calcular qué insumos '
             'hacen falta para una cantidad de café a producir. Ejemplo: para empacar 40 bolsas se consulta '
             'la receta, el material requerido, las existencias y el plazo de reposición antes de programar la producción.',
             reverse('cadena_mrp'), 'Abrir planificación MRP'),
            (['distribucion','despacho','entrega','transporte','pedido','ruta'],
             'El módulo de Distribución organiza el paso del pedido desde la preparación hasta la entrega. '
             'Sirve para identificar el lote enviado, la cantidad, el transportista, el despacho y la recepción. '
             'Ejemplo: un pedido se prepara en almacén, se despacha y solo se marca como entregado cuando '
             'existe confirmación; despachar no equivale a entregar.',
             reverse('cadena_area',args=['distribucion']), 'Abrir Distribución'),
            (['tienda','cliente','venta','catalogo','precio','marca','presentacion'],
             'El módulo de Clientes y tienda publica las marcas, bolsas, pesos y precios del café y registra '
             'ventas en los puntos de venta. Sirve para relacionar cada presentación con su lote y el QR '
             'que explica su procedencia. Ejemplo: una bolsa de 250 g muestra su precio y el historial del '
             'café del que procede. Los precios DEMO no corresponden a transacciones reales.',
             reverse('cadena_area',args=['tienda']), 'Abrir Clientes y tienda'),
            (['qr','trazabilidad','pasaporte'],
             'La trazabilidad une los registros del mismo lote a lo largo de los cinco módulos. El QR '
             'abre su ficha pública para consultar la finca, el método y las etapas efectivamente documentadas. '
             'Para usarlo desde otro celular se necesita una IP accesible en la misma red o una dirección HTTPS pública.',
             reverse('cadena_qrs'), 'Abrir códigos QR'),
        ]
        for palabras, descripcion, destino, etiqueta in conceptos:
            if _contiene(s, palabras):
                return JsonResponse({'respuesta':descripcion, 'url':destino,
                    'etiqueta':etiqueta,
                    'sugerencias':['¿Cómo funciona el almacén?', '¿Para qué sirve producción?',
                                   '¿Cómo funciona distribución?', '¿Cuánto stock de café tenemos?'],
                    'fuente':'Descripción funcional de CaféTrace · no es un saldo ni un registro de operación'},
                    json_dumps_params={'ensure_ascii':False})

    m=_metrics()
    if _contiene(s,['ayuda','guia','guiame','recorrido','paso','areas','area','modulos','funciones']):
        pasos=' '.join(f"{i+1}. {g['titulo'].split('· ',1)[-1]}: {g['descripcion']}" for i,g in enumerate(GUIAS))
        r='Recorrido guiado de la empresa: '+pasos+' Selecciona un área y verifica sus registros antes de avanzar.'
        url=reverse('cadena_empresa_demo') if request.user.is_superuser else reverse('cadena_area',args=['proveedor'])
        e='Abrir recorrido de empresa' if request.user.is_superuser else 'Abrir área'
    elif _contiene(s,['inventario','stock','kardex','existencia','saldo','almacen','bodega']):
        mat=Material.objects.count()
        r=(f'El saldo documental de café es {m["stock_lotes_kg"]:.2f} kg, calculado como entradas menos salidas. '
           f'Existen {mat} materiales registrados. Verifica inventario físico y kardex para confirmar cantidades; '
           'el sistema no afirma que este saldo sea un conteo real.')
        url=reverse('cadena_area',args=['almacen']);e='Consultar almacén'
    elif _contiene(s,['mrp','requerimiento','insumo','material','receta','planificacion','planificar']):
        r=(f'Hay {m["materiales"]} materiales y {m["planes_mrp"]} planes MRP. '
           'Para calcular faltantes: selecciona el lote y la receta, indica la cantidad objetivo y contrasta el requerimiento con existencias y plazos.')
        url=reverse('cadena_mrp');e='Consultar MRP'
    elif _contiene(s,['pedido','despacho','entrega','transporte','distribucion','ruta']):
        r=(f'Hay {m["pedidos"]} pedidos, de los cuales {m["pedidos_pendientes"]} están pendientes. '
           'El flujo correcto es pedido → preparación → despacho → transporte → entrega confirmada. '
           'Un pedido despachado no implica por sí solo que el cliente lo recibió.')
        url=reverse('cadena_area',args=['distribucion']);e='Ver pedidos y distribución'
    elif _contiene(s,['qr','trazabilidad','origen','historia','pasaporte']):
        r=(f'Hay {m["lotes"]} lotes identificados. Cada QR conduce al pasaporte del café, '
           'donde el consumidor consulta finca, método y eventos registrados. '
           'Para escanear desde un celular, usa una dirección HTTPS pública o la IP de tu PC en la misma red; '
           '127.0.0.1 no sirve desde otro dispositivo.')
        url=reverse('cadena_qrs');e='Consultar códigos QR'
    elif _contiene(s,['venta','cliente','tienda','precio','comprar','catalogo','marca','presentacion']):
        r=(f'Hay {m["puntos_venta"]} puntos de venta y {m["ventas"]} ventas registradas. '
           'Puedes explorar tipos de café, marcas, gramajes y precios. '
           'Las operaciones DEMO son ficticias y el catálogo no procesa pagos reales.')
        url=reverse('cadena_catalogo');e='Abrir catálogo'
    elif _contiene(s,['produccion','tueste','tostion','secado','beneficio','fermentacion','procesamiento','empaque']):
        r=(f'Hay {m["procesos"]} procesos registrados en CaféTrace. '
           'Cada registro debe identificar lote, fecha, etapa, entrada y salida, responsable y observaciones. '
           'Los métodos lavado, natural, honey y anaeróbico tienen recorridos distintos.')
        url=reverse('cadena_area',args=['produccion']);e='Abrir producción'
    elif _contiene(s,['proveedor','agricultor','finca','cosecha','recepcion','productor']):
        r=(f'Hay {m["productores"]} productores y {m["recepciones"]} recepciones registradas. '
           'Desde origen se registra finca, lote, peso y fecha antes de continuar hacia beneficio.')
        url=reverse('cadena_area',args=['proveedor']);e='Abrir agricultor y proveedor'
    elif _contiene(s,['alerta','incidencia','problema','error']):
        r=(f'Hay {m["incidencias_abiertas"]} incidencias abiertas. '
           'Revisa la fecha, el área y la causa antes de resolver una desviación; no se eliminan registros históricos.')
        url=reverse('cadena_incidencias');e='Consultar incidencias'
    else:
        r=('Puedo ayudarte con el origen, el lote, sus procesos, MRP, stock, pedidos, precios y QR. '
           'Pregunta por un tema o escribe un código exacto, por ejemplo DEMO-ESP-01. '
           'Soy un asistente guiado basado en registros, no un modelo generativo.')
        url=reverse('cadena_empresa_demo') if request.user.is_superuser else reverse('cadena_catalogo')
        e='Abrir empresa DEMO' if request.user.is_superuser else 'Explorar cafés'
    return JsonResponse({'respuesta':r,'url':url,'etiqueta':e,
        'sugerencias':sugerencias,'fuente':'Registros en la base de datos local · consulta de solo lectura'},
        json_dumps_params={'ensure_ascii':False})
