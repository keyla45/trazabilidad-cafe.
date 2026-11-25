"""Asistente público de solo lectura, restringido al catálogo autorizado."""
import re
import unicodedata
from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from .models import ProductoCatalogo, MarcaCafe, PuntoVenta
from trazabilidad.models import EtapaEspecial, EventoTrazabilidad


def _simple(t):
    return ''.join(x for x in unicodedata.normalize('NFKD', t.casefold()) if not unicodedata.combining(x))


def _tiene(t, palabras):
    return any(re.search(r'(?<!\w)'+re.escape(p)+r'\w*(?!\w)', t) for p in palabras)


@require_GET
def chat_catalogo(request):
    # Limitación por sesión de navegador; evita consultas excesivas de un endpoint anónimo.
    if not request.session.session_key:
        request.session.create()
    key='chat_publico:'+request.session.session_key
    consultas=cache.get(key, 0)
    if consultas>=45:
        return JsonResponse({'respuesta':'Has realizado muchas consultas. Intenta más tarde.'},status=429)
    cache.set(key, consultas+1, 60)
    texto=request.GET.get('q','').strip()[:220]
    sugerencias=['¿Qué cafés están disponibles?', '¿Qué es café honey?', '¿Cuánto cuesta Geisha?', '¿Dónde está la tienda?', '¿Cómo funciona el QR?']
    def r(respuesta, url=None, etiqueta=None):
        return JsonResponse({'respuesta':respuesta,'url':url or reverse('catalogo_publico'),'etiqueta':etiqueta or 'Explorar catálogo','sugerencias':sugerencias,'fuente':'Información comercial publicada de CaféTrace · DEMO cuando corresponda'}, json_dumps_params={'ensure_ascii':False})
    if not texto:
        return r('¡Hola! Puedo explicarte los cafés, precios publicados, marcas, gramajes, fincas, métodos de beneficio y trazabilidad QR. No accedo al inventario interno ni a datos personales.')
    t=_simple(texto)
    productos=ProductoCatalogo.objects.filter(activo=True).select_related('lote','lote__finca','marca')

    # Interpretar primero qué desea saber la persona, no solo si escribió «café».
    # El catálogo no dispone de análisis sensoriales ni de demanda verificable.
    if _tiene(t,['aroma','olor','aromatico','perfume','fragancia']):
        if _tiene(t,['mas','mejor','mayor','intenso','fuerte','recomend','cual']):
            return r('El aroma no se determina solo por la variedad de café: influyen el tueste, el proceso y la preparación. '
                     'Actualmente el catálogo no contiene puntuaciones sensoriales comparables para afirmar qué café tiene más aroma. '
                     'Puedes revisar las descripciones publicadas de cada producto y consultar en su ficha la finca y el método de beneficio. '
                     'Si buscas perfiles afrutados, puedes explorar los cafés de proceso natural; esto es una orientación general, no una medición de estos lotes.',
                     reverse('catalogo_publico'),'Comparar cafés y procesos')
        return r('El aroma es lo que se percibe al oler el café molido o preparado. Puede variar con la variedad, el proceso, '
                 'la frescura, el tueste y la extracción. Consulta la descripción de cada café: no contamos con una cata '
                 'validada que permita asignar una intensidad exacta a las marcas DEMO.')
    if _tiene(t,['sabor','sabe','acidez','amargor','dulzor','notas','perfil']):
        return r('El sabor de un café depende del origen, variedad, beneficio, tueste y preparación. '
                 'Los productos del catálogo muestran finca y proceso, pero no todos tienen una ficha de cata validada. '
                 'No sería correcto atribuirles un sabor exacto sin esa evidencia. Puedes comparar las fichas publicadas.')
    if _tiene(t,['mas vendido','mas popular','mas demandado','preferido','mas comprado']):
        return r('No puedo identificar el café más vendido a partir del catálogo: las presentaciones publicadas no '
                 'son un registro de ventas verificadas. Para conocer la demanda hay que analizar transacciones confirmadas; '
                 'esa información interna no se comparte en el asistente público.')
    if _tiene(t,['barato','economico','menor precio','menos cuesta','mas economico']):
        referencia=productos.filter(gramos=250).order_by('precio_usd','pk').first()
        if referencia:
            detalle=' (precio ficticio DEMO)' if referencia.es_demo else ''
            return r(f'Entre las presentaciones de 250 g publicadas, la de menor precio es '
                     f'{referencia.marca.nombre} · {referencia.titulo}: ${referencia.precio_usd} USD{detalle}. '
                     'La comparación es solo para el mismo gramaje; no significa que tenga menor costo por kilogramo.',
                     reverse('producto_publico',args=[referencia.pk]),'Ver presentación de 250 g')
        return r('No hay presentaciones de 250 g publicadas para hacer una comparación de precio en igualdad de gramaje.')
    if _tiene(t,['para que','como funciona','como se usa','que es']) and _tiene(t,['catalogo','tienda','qr','trazabilidad']):
        if _tiene(t,['qr','trazabilidad']):
            return r('El código QR de cada presentación permite abrir una ficha pública vinculada a su lote. '
                     'Allí se consultan la finca, el método de beneficio y las etapas realmente registradas. '
                     'No es un certificado automático de calidad ni una prueba de que todas las etapas terminaron.')
        return r('El catálogo permite explorar marcas, variedades, gramajes, precios y procedencia sin crear una cuenta. '
                 'Al entrar en una presentación podrás abrir su ficha y consultar el QR de trazabilidad.')
    # Coincidencia exacta por SKU; nunca devolver datos de pedidos o inventario interno.
    skus=re.findall(r'[\w-]{4,70}',texto)
    for token in skus:
        o=productos.filter(sku__iexact=token).first()
        if o:
            return r(f'{o.marca.nombre} · {o.titulo}. {o.especie}, {o.formato}, {o.gramos} g, ${o.precio_usd} USD. Finca: {o.lote.finca.nombre}; proceso: {o.lote.metodo_proceso}. '+('Precio y marca ficticios DEMO. ' if o.es_demo else '')+'Abre el pasaporte para ver únicamente las etapas registradas.',reverse('producto_publico',args=[o.pk]),'Ver ficha y QR')
    # Búsqueda por variedad o marca, priorizada si el usuario nombra un artículo real.
    for o in productos.order_by('id')[:250]:
        palabras=[o.lote.variedad, o.marca.nombre]
        if any(len(x)>=4 and _simple(x) in t for x in palabras):
            similares=productos.filter(Q(lote__variedad__iexact=o.lote.variedad)|Q(marca=o.marca)).order_by('precio_usd')[:5]
            precios=', '.join(f'{x.gramos} g: ${x.precio_usd}' for x in similares)
            return r(f'{o.marca.nombre} ofrece {o.lote.variedad} ({o.especie}), método {o.lote.metodo_proceso}, origen {o.lote.finca.nombre}. Presentaciones publicadas: {precios}. '+('Son precios de demostración. ' if o.es_demo else '')+'En su ficha conocerás la historia del lote y el QR.',reverse('producto_publico',args=[o.pk]),'Ver café y su historia')
    metodos={'lavado':'Se retira la pulpa; el beneficio puede incluir fermentación y lavado antes del secado. El procedimiento exacto depende del lote.',
    'natural':'La cereza se seca con su fruta antes del trillado. Su duración varía según el clima y manejo.',
    'honey':'Se despulpa y se conserva parte del mucílago durante el secado. Los detalles deben constar en la ficha del lote.',
    'anaerobico':'La fermentación se realiza en condiciones de oxígeno limitado y posteriormente continúa el beneficio y secado definido para ese lote.'}
    for nombre,detalle in metodos.items():
        if _tiene(t,[nombre]):
            cuantos=productos.filter(lote__metodo_proceso__iexact=nombre.capitalize() if nombre!='anaerobico' else 'Anaeróbico').values('lote_id').distinct().count()
            return r(f'Proceso {nombre}: {detalle} Actualmente hay {cuantos} lotes de este método publicados en el catálogo.')
    if _tiene(t,['qr','trazabilidad','historia','proceso','procesamiento','origen','finca']):
        return r('Selecciona una bolsa y pulsa «Ver marca, finca, proceso y QR». La ficha pública muestra origen, método, etapas finalizadas, fechas y eventos documentados. El QR abre esa misma página; desde otro celular se necesita una dirección accesible en la red.')
    if _tiene(t,['precio','cuesta','valor','gramo','presentacion','bolsa','costo']):
        minp=productos.order_by('precio_usd').first()
        maxp=productos.order_by('-precio_usd').first()
        if minp and maxp:
            return r(f'Los precios publicados van desde ${minp.precio_usd} hasta ${maxp.precio_usd} USD según café, marca y gramaje. Las presentaciones y sus precios pueden ser ficticios DEMO. Selecciona un café para ver su valor exacto.')
        return r('Aún no hay precios publicados. El administrador debe cargar presentaciones comerciales.')
    if _tiene(t,['tienda','comprar','ubicacion','direccion','donde','sucursal']):
        puntos=list(PuntoVenta.objects.filter(es_demo=True)[:4])
        if puntos:
            return r('Puntos de venta de demostración: '+ '; '.join(f'{x.nombre} ({x.ciudad})' for x in puntos)+'. Son ubicaciones ficticias; no hay compras ni pagos reales.', reverse('catalogo_publico')+'#puntos', 'Ver puntos de venta')
        return r('No hay puntos de venta publicados todavía.')
    if _tiene(t,['tipo','especie','marca','cafe','catalogo','producto','disponible','opcion']):
        n=productos.count(); marcas=MarcaCafe.objects.filter(activa=True).count()
        return r(f'El catálogo contiene {n} presentaciones activas de {marcas} marcas registradas. Puedes filtrar por especie, método, marca o formato. Los registros DEMO son ficticios.')
    return r('Puedo ayudarte sobre cafés, marcas, origen, métodos lavado/natural/honey/anaeróbico, precios, presentaciones, tiendas ficticias y QR. No tengo acceso a datos privados ni soy un modelo generativo. Prueba una pregunta sugerida.')
