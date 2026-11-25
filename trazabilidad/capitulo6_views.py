"""Seguimiento del capítulo 6 basado en datos existentes, sin inventar resultados."""
import csv
from collections import Counter
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import (Lote, PerfilEspecial, EtapaEspecial, PresentacionCafe,
                     LecturaSensor, RecepcionCereza, MovimientoInventario,
                     Pedido, Transporte, EvaluacionExperimental, GenealogiaLote)
from .especial_flujos import FLUJOS


def _es_demo(lote):
    return lote.codigo.startswith('DEMO-') or 'DEMO' in (lote.notas or '').upper()


def _calidad_dato(lote):
    """Completitud documental (no equivale a calidad de taza)."""
    etapas = lote.etapas_especiales.count()
    catacion = PerfilEspecial.objects.filter(lote=lote).first()
    pruebas = [
        ('Productor identificado', bool(lote.productor_id)),
        ('Finca identificada', bool(lote.finca_id)),
        ('Altitud registrada', lote.finca.altura_msnm is not None),
        ('Fecha de cosecha', bool(lote.fecha_cosecha)),
        ('Método de beneficio', lote.metodo_proceso in FLUJOS),
        ('Recepción registrada', lote.recepciones.exists()),
        ('Etapas de proceso registradas', etapas > 0),
        ('Humedad final registrada', lote.humedad is not None),
        ('Catación documentada', bool(catacion and catacion.puntaje_total is not None)),
        ('Presentación comercial registrada', lote.presentaciones_especiales.exists()),
    ]
    return {'porcentaje': round(sum(ok for _,ok in pruebas)*100/len(pruebas)),
            'campos': [{'nombre':n,'completo':ok} for n,ok in pruebas]}


@login_required
def centro(request):
    qs = Lote.objects.select_related('productor','finca').all()
    metodo = request.GET.get('metodo','')
    busqueda = request.GET.get('q','').strip()[:80]
    origen = request.GET.get('origen','todos')
    if metodo in FLUJOS: qs = qs.filter(metodo_proceso=metodo)
    if busqueda: qs=qs.filter(Q(codigo__icontains=busqueda)|Q(variedad__icontains=busqueda)|Q(finca__nombre__icontains=busqueda)|Q(productor__nombre__icontains=busqueda))
    if origen=='demo': qs=qs.filter(codigo__startswith='DEMO-')
    elif origen=='real': qs=qs.exclude(codigo__startswith='DEMO-')
    counts = dict(Lote.objects.values_list('metodo_proceso').annotate(n=Count('pk')))
    fichas=[]
    for lote in qs[:80]:
        cd=_calidad_dato(lote)
        fichas.append({'lote':lote,'demo':_es_demo(lote),'completitud':cd['porcentaje'],
                       'etapas':lote.etapas_especiales.count(),
                       'perfil':PerfilEspecial.objects.filter(lote=lote).first(),
        'origenes':GenealogiaLote.objects.filter(lote_resultante=lote).select_related('lote_origen'),
        'derivados':GenealogiaLote.objects.filter(lote_origen=lote).select_related('lote_resultante')})
    experimentos=[]
    for codigo,titulo,desc in [
        ('E1','Control de secado','Dispersión de humedad final y lotes fuera del rango definido'),
        ('E2','Predicción de calidad','MAE y R² usando lotes de prueba separados del entrenamiento'),
        ('E3','Valor del origen digital','Escaneos, intención de compra y precio aceptado')]:
        experimentos.append({'codigo':codigo,'titulo':titulo,'descripcion':desc,
            'registros':EvaluacionExperimental.objects.filter(experimento=codigo).count()})
    contexto={
        'fichas':fichas,'metodo':metodo,'origen':origen,'busqueda':busqueda,
        'total_lotes':Lote.objects.count(),
        'demo_lotes':Lote.objects.filter(codigo__startswith='DEMO-').count(),
        'reales_lotes':Lote.objects.exclude(codigo__startswith='DEMO-').count(),
        'cataciones':PerfilEspecial.objects.count(),
        'lecturas':LecturaSensor.objects.count(),
        'presentaciones':PresentacionCafe.objects.count(),
        'pedidos':Pedido.objects.count(),
        'transportes':Transporte.objects.count(),
        'categorias':[{'nombre':m,'cantidad':counts.get(m,0),'etapas':len(e)} for m,e in FLUJOS.items()],
        'experimentos':experimentos,
    }
    return render(request,'capitulo6/centro.html',contexto)


@login_required
def auditoria(request,lote_id):
    lote=get_object_or_404(Lote.objects.select_related('productor','finca'),pk=lote_id)
    calidad=_calidad_dato(lote)
    registros=lote.etapas_especiales.all()
    flujo=[]
    for i,n in enumerate(FLUJOS.get(lote.metodo_proceso,[]),1):
        e=next((e for e in registros if e.orden==i),None)
        flujo.append({'numero':i,'nombre':n,'registro':e})
    contexto={'lote':lote,'demo':_es_demo(lote),'calidad':calidad,
        'flujo':flujo,'lecturas':lote.lecturas.all()[:20],
        'recepciones':lote.recepciones.all()[:20],
        'eventos':lote.eventos.all().order_by('-fecha')[:30],
        'inventarios':lote.movimientos.all()[:20],
        'pedidos':lote.pedidos.all()[:20],
        'perfil':PerfilEspecial.objects.filter(lote=lote).first(),
        'origenes':GenealogiaLote.objects.filter(lote_resultante=lote).select_related('lote_origen'),
        'derivados':GenealogiaLote.objects.filter(lote_origen=lote).select_related('lote_resultante')}
    return render(request,'capitulo6/auditoria.html',contexto)


@login_required
def exportar(request):
    """CSV completo de control documental para análisis posterior en Power BI."""
    res=HttpResponse(content_type='text/csv; charset=utf-8')
    res['Content-Disposition']='attachment; filename="cafetrace_capitulo6_control_datos.csv"'
    res.write('\ufeff')
    wr=csv.writer(res)
    wr.writerow(['lote','tipo_dato','productor','finca','altitud_msnm','variedad','metodo',
                 'cosecha','humedad_final_pct','catacion_puntos','completitud_documental_pct',
                 'etapas_registradas','presentaciones','fuente'])
    for lote in Lote.objects.select_related('productor','finca').all().iterator():
        perfil=PerfilEspecial.objects.filter(lote=lote).first()
        wr.writerow([lote.codigo,'DEMO' if _es_demo(lote) else 'REGISTRO OPERATIVO',
            lote.productor.nombre,lote.finca.nombre,lote.finca.altura_msnm or '',
            lote.variedad,lote.metodo_proceso,lote.fecha_cosecha,
            lote.humedad if lote.humedad is not None else '',
            perfil.puntaje_total if perfil else '',_calidad_dato(lote)['porcentaje'],
            lote.etapas_especiales.count(),lote.presentaciones_especiales.count(),
            'CaféTrace Django'])
    return res
