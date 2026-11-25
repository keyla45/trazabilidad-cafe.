from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from .models import Lote, Pedido, LecturaSensor, EventoTrazabilidad, PresentacionCafe

@login_required
def recorrido_demo(request):
    lotes=list(Lote.objects.filter(codigo__startswith='DEMO-ESP-').select_related('productor','finca').order_by('codigo'))
    ejemplos=[]
    for lote in lotes:
        ejemplos.append({'lote':lote,'etapas':lote.etapas_especiales.count(),
            'finalizadas':lote.etapas_especiales.filter(estado='Finalizada').count(),
            'eventos':lote.eventos.count(),'sensores':lote.lecturas.count(),
            'pedidos':lote.pedidos.count(),'formatos':lote.presentaciones_especiales.count()})
    return render(request,'demo/recorrido.html',{'ejemplos':ejemplos,
        'total_demo':len(lotes),'total_lecturas':LecturaSensor.objects.filter(lote__codigo__startswith='DEMO-ESP-').count(),
        'total_pedidos':Pedido.objects.filter(lote__codigo__startswith='DEMO-ESP-').count(),
        'total_eventos':EventoTrazabilidad.objects.filter(lote__codigo__startswith='DEMO-ESP-').count()})
