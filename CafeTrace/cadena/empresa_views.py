"""Panel integrado de demostración de una empresa cafetera ficticia."""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render
from django.utils import timezone
from trazabilidad.models import (Lote, Productor, Finca, RecepcionCereza, EtapaEspecial,
   ControlCalidad, EventoTrazabilidad, Pedido, Transporte, MovimientoInventario, PresentacionCafe)
from cadena.models import PuntoVenta, VentaTienda, Material, PlanProduccion, Incidencia

@login_required
def empresa(request):
    lotes=Lote.objects.filter(codigo__startswith='DEMO-ESP-').select_related('productor','finca').order_by('codigo')
    datos=[]
    for l in lotes:
        mov=l.movimientos.aggregate(entradas=Sum('cantidad_kg',filter=Q(tipo='Entrada')),
                                   salidas=Sum('cantidad_kg',filter=Q(tipo='Salida')))
        saldo=(mov['entradas'] or Decimal('0'))-(mov['salidas'] or Decimal('0'))
        datos.append({'lote':l,'eventos':l.eventos.count(),
                      'procesos':l.etapas_especiales.filter(estado='Finalizada').count(),
                      'etapas':l.etapas_especiales.count(),
                      'saldo':saldo,'pedidos':l.pedidos.count(),
                      'presentaciones':l.presentaciones_especiales.count()})
    eventos=EventoTrazabilidad.objects.filter(lote__codigo__startswith='DEMO-ESP-').select_related('lote').order_by('-fecha')[:12]
    ventas=VentaTienda.objects.filter(es_demo=True).select_related('lote','punto_venta').order_by('-fecha')[:8]
    puntos=PuntoVenta.objects.filter(es_demo=True).order_by('tipo','nombre')
    pedidos=Pedido.objects.filter(lote__codigo__startswith='DEMO-ESP-').select_related('lote').order_by('-fecha')[:8]
    return render(request,'cadena/empresa_demo.html',{
        'lotes_demo':datos,'eventos_demo':eventos,'ventas_demo':ventas,
        'puntos_demo':puntos,'pedidos_demo':pedidos,
        'numero_lotes':len(datos),'numero_puntos':puntos.count(),
        'numero_ventas':ventas.count(),
        'total_etapas':EtapaEspecial.objects.filter(lote__codigo__startswith='DEMO-ESP-',estado='Finalizada').count(),
        'total_entradas':MovimientoInventario.objects.filter(lote__codigo__startswith='DEMO-ESP-',tipo='Entrada').count(),
        'es_admin':request.user.is_superuser,
    })
