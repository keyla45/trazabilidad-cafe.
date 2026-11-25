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
