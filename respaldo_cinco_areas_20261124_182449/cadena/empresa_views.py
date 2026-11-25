"""Panel integrado de demostración de una empresa cafetera ficticia."""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from trazabilidad.models import (Lote, Productor, Finca, RecepcionCereza, ProcesoCafe, EtapaEspecial,
   ControlCalidad, EventoTrazabilidad, Pedido, Transporte, MovimientoInventario, PresentacionCafe)
from cadena.models import PuntoVenta, VentaTienda, Material, PlanProduccion, Incidencia, MovimientoMaterial, RecetaMaterial, ProductoCatalogo

@login_required
def empresa(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden('El recorrido administrativo DEMO es exclusivo de administración.')
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


# Centro operativo DEMO: cinco ventanas internas de la misma empresa.
# Son vistas sobre registros, no una simulación de transacciones automáticas.
DEMO_AREAS = {
    'proveedor': {'numero':'01','titulo':'Finca y agricultor','subtitulo':'Cosecha, recepción y beneficio de café','responsable':'Juan Pérez · Agricultor','icono':'🌱','etapas':['Cosecha','Recepción','Selección','Despulpado','Fermentación','Lavado','Secado'],'descripcion':'Se identifica el productor y se documenta el beneficio según el método del lote.'},
    'produccion': {'numero':'02','titulo':'Producción y logística','subtitulo':'Trilla, tostión, empaque y planificación MRP','responsable':'Carlos Méndez · Operario de planta','icono':'🔥','etapas':['Trilla','Clasificación','Tostión','Empaque'],'descripcion':'Los procesos transforman el café en presentaciones comerciales y requieren insumos.'},
    'almacen': {'numero':'03','titulo':'Almacén e inventario','subtitulo':'Ingresos, salidas, ubicaciones y existencias','responsable':'Lucía Herrera · Responsable de bodega','icono':'📦','etapas':['Recepción a bodega','Control de existencias','Preparación de salida'],'descripcion':'Se registran entradas y salidas del mismo lote, con historial consultable.'},
    'distribucion': {'numero':'04','titulo':'Distribución','subtitulo':'Pedidos, despachos, transporte y entregas','responsable':'David Rosero · Coordinador logístico','icono':'🚚','etapas':['Pedido','Preparación','Despacho','Transporte','Entrega'],'descripcion':'La salida de bodega se relaciona con el pedido y su destino comercial.'},
    'tienda': {'numero':'05','titulo':'Clientes y tienda física','subtitulo':'Puntos de venta, marcas, precios, gramajes y QR','responsable':'Andrea Rosales · Encargada de tienda','icono':'🏪','etapas':['Recepción en tienda','Exhibición','Venta','Consulta QR'],'descripcion':'El comprador puede ver el producto en el catálogo y consultar su procedencia.'},
}

@login_required
def empresa_area(request, area):
    if not request.user.is_superuser:
        return HttpResponseForbidden('Acceso exclusivo de administración.')
    if area not in DEMO_AREAS:
        from django.http import Http404
        raise Http404('Área DEMO inexistente')
    datos=DEMO_AREAS[area]
    lotes=list(Lote.objects.filter(codigo__startswith='DEMO-ESP-').select_related('finca','productor').order_by('codigo')[:4])
    elegible=request.GET.get('lote','')
    lote=next((l for l in lotes if l.codigo==elegible),lotes[0] if lotes else None)
    entradas=salidas=0
    saldo=0
    if lote:
        movimiento=lote.movimientos.aggregate(entradas=Sum('cantidad_kg',filter=Q(tipo='Entrada')),salidas=Sum('cantidad_kg',filter=Q(tipo='Salida')))
        entradas=movimiento['entradas'] or 0
        salidas=movimiento['salidas'] or 0
        saldo=entradas-salidas
    eventos=list(lote.eventos.order_by('fecha')) if lote else []
    etapas_lote=list(lote.etapas_especiales.order_by('orden')) if lote else []
    movimientos=list(lote.movimientos.order_by('-fecha')[:12]) if lote else []
    planes=list(PlanProduccion.objects.filter(lote=lote).order_by('-fecha_programada')) if lote else []
    pedidos=list(lote.pedidos.order_by('-fecha')[:10]) if lote else []
    ventas=list(VentaTienda.objects.filter(lote=lote,es_demo=True).select_related('punto_venta').order_by('-fecha')[:10]) if lote else []
    ofertas=list(ProductoCatalogo.objects.filter(lote=lote,activo=True,es_demo=True).select_related('marca').order_by('gramos')[:18]) if lote else []
    acciones={
     'proveedor':[('Productores','lista_productores'),('Fincas','lista_fincas'),('Registrar recepción','modulo_nuevo','recepciones'),('Consultar lotes','lista_lotes')],
     'produccion':[('Procesos','modulo','procesos'),('Planificación MRP','cadena_mrp'),('Catación','lista_calidad'),('Detalle técnico','especial_detalle',lote.id if lote else 0)],
     'almacen':[('Inventario de lotes','modulo','inventario'),('Inventario de materiales','cadena_area','almacen'),('Planificación de insumos','cadena_mrp')],
     'distribucion':[('Pedidos','modulo','pedidos'),('Transportes','modulo','transportes'),('Área de distribución','cadena_area','distribucion')],
     'tienda':[('Catálogo público','catalogo_publico'),('Marcas y presentaciones','cadena_presentaciones'),('Puntos de venta','cadena_puntos'),('Ventas','cadena_area','tienda')],
    }
    botones=[]
    for item in acciones[area]:
        if item[1]=='especial_detalle' and not lote:continue
        botones.append({'titulo':item[0],'url':reverse(item[1],args=[item[2]]) if len(item)==3 else reverse(item[1])})
    # Registros y cifras siempre desde la base, no números visuales inventados.
    return render(request,'cadena/empresa_area.html',{
      'area':area,'info':datos,'areas':DEMO_AREAS,'lotes':lotes,'lote':lote,
      'eventos':eventos,'etapas_lote':etapas_lote,'movimientos':movimientos,'planes':planes,
      'pedidos':pedidos,'ventas':ventas,'ofertas':ofertas,'entradas':entradas,'salidas':salidas,'saldo':saldo,
      'botones':botones,'puntos':PuntoVenta.objects.filter(es_demo=True)[:6],
      'materiales':Material.objects.filter(es_demo=True)[:8],
      'movimientos_materiales':MovimientoMaterial.objects.filter(material__es_demo=True).select_related('material').order_by('-fecha')[:8],
      'incidencias':Incidencia.objects.filter(lote=lote)[:6] if lote else [],
    })
