"""Catálogo y fichas públicas. Sin autenticación; excluye datos privados."""
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlsplit
from trazabilidad.models import Lote, PresentacionCafe, PerfilEspecial, ControlCalidad, EventoTrazabilidad, EtapaEspecial
from cadena.models import PuntoVenta, VentaTienda


def catalogo_publico(request):
    q = request.GET.get('q', '').strip()[:80]
    metodo = request.GET.get('metodo', '')
    lotes = Lote.objects.select_related('finca').prefetch_related('presentaciones_especiales').all()
    if q:
        lotes = lotes.filter(Q(variedad__icontains=q)|Q(codigo__icontains=q)|Q(finca__nombre__icontains=q))
    if metodo in dict(Lote.METODOS):
        lotes = lotes.filter(metodo_proceso=metodo)
    cards = []
    for lote in lotes[:80]:
        presentaciones = list(lote.presentaciones_especiales.all())
        cards.append({'lote':lote,'presentaciones':presentaciones,
          'precio_minimo':min((p.precio_usd for p in presentaciones if p.precio_usd is not None),default=None),
          'disponibles':sum(p.unidades for p in presentaciones)})
    puntos = PuntoVenta.objects.filter(es_demo=True)[:5]
    return render(request,'publico/catalogo.html',{
        'cards':cards,'q':q,'metodo':metodo,'metodos':Lote.METODOS,'puntos':puntos,
        'total':len(cards), 'demo':True})


def catalogo_publico(request):
    """Catálogo real desde la base de datos. Los valores DEMO se etiquetan."""
    from cadena.models import MarcaCafe, ProductoCatalogo
    q = request.GET.get('q','').strip()[:80]
    metodo = request.GET.get('metodo','')
    especie = request.GET.get('especie','')
    marca_id = request.GET.get('marca','')
    formato = request.GET.get('formato','')
    ofertas = ProductoCatalogo.objects.filter(activo=True).select_related('lote','lote__finca','marca')
    if q:
        ofertas=ofertas.filter(Q(titulo__icontains=q)|Q(lote__variedad__icontains=q)|Q(lote__finca__nombre__icontains=q)|Q(marca__nombre__icontains=q)|Q(sku__icontains=q))
    if metodo in dict(Lote.METODOS): ofertas=ofertas.filter(lote__metodo_proceso=metodo)
    if especie in ('Arábica','Robusta','Libérica','Excelsa'): ofertas=ofertas.filter(especie=especie)
    if formato in ('Grano','Molido','Verde'): ofertas=ofertas.filter(formato=formato)
    if marca_id.isdecimal(): ofertas=ofertas.filter(marca_id=int(marca_id))
    # Agrupación por marca + lote: cada tarjeta tiene presentaciones y precios reales del registro.
    agrupadas={}
    for oferta in ofertas.order_by('marca__nombre','lote__codigo','gramos')[:600]:
        llave=(oferta.marca_id,oferta.lote_id)
        if llave not in agrupadas:
            agrupadas[llave]={'lote':oferta.lote,'marca':oferta.marca,'especie':oferta.especie,
               'categoria':oferta.categoria,'ofertas':[],'precio_minimo':oferta.precio_usd,'disponibles':0,
               'ejemplo':oferta}
        grupo=agrupadas[llave]
        grupo['ofertas'].append(oferta)
        grupo['precio_minimo']=min(grupo['precio_minimo'],oferta.precio_usd)
        grupo['disponibles']+=oferta.unidades
    return render(request,'publico/catalogo.html',{
       'cards':list(agrupadas.values()),'total':len(agrupadas),'q':q,'metodo':metodo,
       'especie':especie,'marca_id':marca_id,'formato':formato,
       'metodos':Lote.METODOS,'especies':['Arábica','Robusta','Libérica','Excelsa'],
       'formatos':['Grano','Molido','Verde'],'marcas':MarcaCafe.objects.filter(activa=True),
       'puntos':PuntoVenta.objects.filter(es_demo=True)[:6],
    })


def cafe_publico(request, lote_id):
    lote=get_object_or_404(Lote.objects.select_related('finca'),pk=lote_id)
    presentaciones=lote.presentaciones_especiales.all()
    perfil=PerfilEspecial.objects.filter(lote=lote,decision='Aprobado').first()
    eventos=list(EventoTrazabilidad.objects.filter(lote=lote).order_by('fecha'))
    etapas=list(EtapaEspecial.objects.filter(lote=lote,estado='Finalizada').order_by('orden'))
    puntos=PuntoVenta.objects.filter(ventas__lote=lote).distinct()[:6]
    base=(getattr(settings,'CAFETRACE_PUBLIC_BASE_URL','') or '').strip().rstrip('/')
    parts=urlsplit(base) if base else None
    route=reverse('cafe_publico',args=[lote.id])
    if parts and parts.scheme in ('https','http') and parts.netloc and not parts.username and not parts.password:
        qr_destino=base+route
    else:
        qr_destino=request.build_absolute_uri(route)
    qr_local=urlsplit(qr_destino).hostname in ('127.0.0.1','localhost','0.0.0.0')
    return render(request,'publico/cafe.html',{
       'lote':lote,'presentaciones':presentaciones,'perfil':perfil,'eventos':eventos,
       'etapas':etapas,'puntos':puntos,'es_demo':lote.codigo.startswith('DEMO-'),
       'qr_destino':qr_destino, 'qr_local':qr_local,
    })


def producto_publico(request, producto_id):
    from cadena.models import ProductoCatalogo
    producto = get_object_or_404(ProductoCatalogo.objects.select_related('lote','lote__finca','lote__productor','marca'),pk=producto_id,activo=True)
    lote=producto.lote
    # Sólo los datos de operación documentados son publicados.
    etapas=list(EtapaEspecial.objects.filter(lote=lote,estado='Finalizada').order_by('orden'))
    eventos=list(EventoTrazabilidad.objects.filter(lote=lote).order_by('fecha'))
    perfil=PerfilEspecial.objects.filter(lote=lote,decision='Aprobado').first()
    hermanos=ProductoCatalogo.objects.filter(lote=lote,marca=producto.marca,activo=True).order_by('gramos','formato')
    puntos=PuntoVenta.objects.filter(ventas__lote=lote).distinct()[:6]
    url=crear_url_publica(request, reverse('producto_publico',args=[producto.id]))
    return render(request,'publico/producto.html',{
        'producto':producto,'lote':lote,'perfil':perfil,'etapas':etapas,'eventos':eventos,
        'ofertas':hermanos,'puntos':puntos,'qr_destino':url,
        'qr_local':urlsplit(url).hostname in ('127.0.0.1','localhost','0.0.0.0'),
    })


def crear_url_publica(request, ruta):
    base=(getattr(settings,'CAFETRACE_PUBLIC_BASE_URL','') or '').strip().rstrip('/')
    partes=urlsplit(base) if base else None
    if partes and partes.scheme in ('http','https') and partes.netloc and not partes.username and not partes.password:
        return base+ruta
    return request.build_absolute_uri(ruta)


def producto_qr(request, producto_id):
    import qrcode
    from io import BytesIO
    from django.http import HttpResponse
    from cadena.models import ProductoCatalogo
    producto=get_object_or_404(ProductoCatalogo,pk=producto_id,activo=True)
    url=crear_url_publica(request,reverse('producto_publico',args=[producto.id]))
    qr=qrcode.QRCode(version=None,error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=8,border=3)
    qr.add_data(url);qr.make(fit=True)
    imagen=qr.make_image(fill_color='#352015',back_color='white')
    buffer=BytesIO();imagen.save(buffer,format='PNG')
    response=HttpResponse(buffer.getvalue(),content_type='image/png')
    response['Cache-Control']='no-store'
    return response
