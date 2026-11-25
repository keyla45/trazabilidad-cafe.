from collections import defaultdict
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render,redirect,get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from trazabilidad.models import (Lote,Productor,Finca,RecepcionCereza,ProcesoCafe,ControlCalidad,
  MovimientoInventario,Pedido,Transporte,PresentacionCafe,EventoTrazabilidad)
from trazabilidad.permissions import roles_for
from .models import Material,MovimientoMaterial,RecetaMaterial,PlanProduccion,PuntoVenta,VentaTienda,Incidencia
from .forms import MaterialForm,MovimientoForm,RecetaForm,PlanForm,PuntoVentaForm,VentaForm,IncidenciaForm

AREAS={
 'proveedor':('Agricultor y proveedor','Origen, fincas y recepción del café','sprout'),
 'produccion':('Producción y logística','Transformación de lotes y planificación MRP','factory'),
 'almacen':('Almacén','Existencias, materiales y movimientos','warehouse'),
 'distribucion':('Distribución','Pedidos, despachos y entregas','truck'),
 'tienda':('Tienda y punto de venta','Catálogo comercial y ventas trazables','store'),
}
ROLE_READ={
 'proveedor':{'Productor','Bodega','Control de calidad'},
 'produccion':{'Bodega','Control de calidad'},
 'almacen':{'Bodega'},
 'distribucion':{'Bodega','Transportista'},
 'tienda':{'Bodega','Cliente','Transportista'},
}
ROLE_WRITE={
 'material':{'Bodega'},'movimiento':{'Bodega'},'receta':{'Bodega'},'plan':{'Bodega'},
 'punto':{'Bodega'},'venta':{'Bodega'},'incidencia':{'Productor','Bodega','Transportista','Control de calidad'},
}
FORMS={'material':MaterialForm,'movimiento':MovimientoForm,'receta':RecetaForm,'plan':PlanForm,
       'punto':PuntoVentaForm,'venta':VentaForm,'incidencia':IncidenciaForm}
DESTINOS={'material':'almacen','movimiento':'almacen','receta':'produccion','plan':'produccion',
          'punto':'tienda','venta':'tienda','incidencia':'tienda'}

def access(request,allowed):
    return request.user.is_superuser or bool(roles_for(request.user)&allowed)

def stock_materiales():
    totales=MovimientoMaterial.objects.values('material_id','tipo').annotate(total=Sum('cantidad'))
    saldos=defaultdict(lambda:Decimal('0'))
    for fila in totales:saldos[fila['material_id']]+=(fila['total'] if fila['tipo']=='Entrada' else -fila['total'])
    return saldos

def stock_lotes():
    totales=MovimientoInventario.objects.values('lote_id','tipo').annotate(total=Sum('cantidad_kg'))
    saldos=defaultdict(lambda:Decimal('0'))
    for f in totales:saldos[f['lote_id']]+=(f['total'] if f['tipo']=='Entrada' else -f['total'])
    return saldos

# Herramientas agrupadas por área, sin duplicar módulos en el menú global.
# Cada acción enlaza a una vista existente de Django.
ACCIONES = {
 'proveedor': [
  ('Cosechas y lotes','Finca, cosecha y lote de origen','crear_lote',None,'🌱'),
  ('Productores','Alta y consulta de agricultores','lista_productores',None,'👨‍🌾'),
  ('Fincas y parcelas','Origen y características del cultivo','lista_fincas',None,'🌿'),
  ('Recepción','Peso, inspección y observaciones','modulo', 'recepciones','📥'),
  ('Beneficio','Despulpado, fermentación, lavado y secado','modulo','procesos','🫘'),
  ('Seguimiento del beneficio','Métodos y etapas por lote','especial_catalogo',None,'📈'),
  ('Insumos y requerimientos','Cantidades para el proceso','cadena_mrp',None,'🧾'),
  ('QR del origen','Consultar historial y procedencia','lista_lotes',None,'▦')],
 'produccion': [
  ('Órdenes de producción','Programación de cantidades','cadena_nuevo','plan','📋'),
  ('Trilla y clasificación','Registrar operaciones por lote','modulo','procesos','⚙️'),
  ('Tostión','Registrar perfil y operación','modulo_nuevo','procesos','🔥'),
  ('Empaque y presentaciones','SKU, producto verde, tostado o molido','especial_catalogo',None,'📦'),
  ('Operarios y actividades','Responsables y tiempos de operación','modulo','procesos','👷'),
  ('MRP / materiales','Recetas, necesidades y faltantes','cadena_mrp',None,'🧮'),
  ('Calidad y catación','Evaluación del café','lista_calidad',None,'☕'),
  ('Costos e incidencias','Registrar novedades de producción','cadena_incidencias',None,'🧾')],
 'almacen': [
  ('Inventario de lotes','Café verde y terminado','modulo','inventario','🏷️'),
  ('Insumos y materiales','Registrar materiales de empaque','cadena_nuevo','material','📦'),
  ('Entradas y salidas','Registrar movimiento de materiales','cadena_nuevo','movimiento','⇄'),
  ('Movimientos de café','Consulta del kardex de lotes','modulo','inventario','📊'),
  ('Mínimos y faltantes','Revisar reposición por MRP','cadena_mrp',None,'⚠️'),
  ('Incidencias','Diferencias de inventario','cadena_incidencias',None,'📑')],
 'distribucion': [
  ('Pedidos','Solicitudes y estados','modulo','pedidos','🧺'),
  ('Preparación','Ver cantidades a despachar','modulo','pedidos','📋'),
  ('Transporte','Vehículos, salida y entrega','modulo','transportes','🚚'),
  ('Registrar transporte','Nuevo registro de envío','modulo_nuevo','transportes','➕'),
  ('Historial de despachos','Seguimiento de la cadena','lista_lotes',None,'↗'),
  ('Incidencias','Novedades o devoluciones','cadena_incidencias',None,'⚠️')],
 'tienda': [
  ('Catálogo de cafés','Explorar cafés y presentaciones','cadena_catalogo',None,'☕'),
  ('Puntos de venta','Tiendas, cafeterías, mayoristas y minoristas','cadena_puntos',None,'🏬'),
  ('Nueva venta','Registrar productos y cantidades','cadena_nuevo','venta','🛒'),
  ('Presentaciones','Grano, molido, formatos y precios','cadena_presentaciones',None,'📦'),
  ('Pedidos comerciales','Venta vinculada al despacho','modulo','pedidos','🧾'),
  ('QR para clientes','Pasaporte del café y etapas verificables','cadena_qrs',None,'▦')]
}

def _acciones_para(area):
    resultado=[]
    for titulo,desc,nombre,arg,ico in ACCIONES.get(area, []):
        if nombre=='cadena_nuevo':
            link=reverse(nombre,args=[area,arg])
        elif arg:
            link=reverse(nombre,args=[arg])
        else:
            link=reverse(nombre)
        resultado.append({'titulo':titulo,'desc':desc,'url':link,'icono':ico})
    return resultado

@login_required
def inicio(request):
    # El centro de las cinco áreas es exclusivo de administración.
    if not request.user.is_superuser:
        roles = roles_for(request.user)
        for nombre, permitidos in ROLE_READ.items():
            if roles & permitidos:
                return redirect('cadena_area', area=nombre)
        return redirect('cadena_catalogo')
    datos={
      'areas':[(slug,*item) for slug,item in AREAS.items()],
      'k_lotes':Lote.objects.count(),'k_productores':Productor.objects.count(),
      'k_stock':sum(stock_lotes().values(),Decimal('0')),
      'k_pedidos':Pedido.objects.exclude(estado__in=['Entregado','Cancelado']).count(),
      'k_ventas':VentaTienda.objects.count(),'k_incidentes':Incidencia.objects.filter(estado='Abierta').count(),
      'ultimos_lotes':Lote.objects.select_related('productor','finca')[:6],
      'ultimos_pedidos':Pedido.objects.select_related('lote').order_by('-fecha')[:6],
      'ultimas_incidencias':Incidencia.objects.order_by('-registrada')[:5],
      'tipos_proceso':Lote.objects.values('metodo_proceso').annotate(total=Count('id')).order_by('-total'),
    }
    return render(request,'cadena/inicio.html',datos)

@login_required
def area(request,area):
    if area not in AREAS:raise Http404('Área desconocida')
    if not access(request,ROLE_READ[area]):return HttpResponseForbidden('Sin autorización para esta área.')
    ctx={'area':area,'titulo':AREAS[area][0],'subtitulo':AREAS[area][1],
         'puede_editar':access(request,ROLE_READ[area]),'stock':stock_lotes(),
         'es_admin':request.user.is_superuser,'acciones':_acciones_para(area)}
    if area=='proveedor':
        ctx.update(productores=Productor.objects.all()[:40],fincas=Finca.objects.select_related('productor')[:30],
                   recepciones=RecepcionCereza.objects.select_related('lote')[:12],lotes=Lote.objects.select_related('finca')[:8],
                   total=Productor.objects.count())
    if area=='produccion':
        ctx.update(procesos=ProcesoCafe.objects.select_related('lote')[:16],planes=PlanProduccion.objects.select_related('lote')[:12],
                   recetas=RecetaMaterial.objects.select_related('material').all()[:20],
                   etapas=Lote.objects.values('metodo_proceso').annotate(total=Count('id')),total=ProcesoCafe.objects.count())
    if area=='almacen':
        saldos=stock_materiales()
        ctx.update(materiales=[{'obj':m,'saldo':saldos[m.id],'bajo':saldos[m.id]<m.stock_minimo} for m in Material.objects.all()],
                   movimientos=MovimientoMaterial.objects.select_related('material')[:15],
                   movimientos_lote=MovimientoInventario.objects.select_related('lote')[:12],
                   lotes=[{'lote':l,'cantidad':stock_lotes()[l.id]} for l in Lote.objects.all()[:20]],
                   total=Material.objects.count())
    if area=='distribucion':
        ctx.update(pedidos=Pedido.objects.select_related('lote').order_by('-fecha')[:30],
                   transportes=Transporte.objects.select_related('lote','pedido')[:12],total=Pedido.objects.count())
    if area=='tienda':
        puntos=PuntoVenta.objects.all().order_by('nombre')
        ventas=VentaTienda.objects.select_related('lote','punto_venta').order_by('-fecha')
        presentaciones=PresentacionCafe.objects.select_related('lote','lote__finca').order_by('-id')
        ctx.update(puntos=puntos[:30],ventas=ventas[:20],presentaciones=presentaciones[:12],
                   total=ventas.count(),lotes=Lote.objects.select_related('finca')[:8],
                   num_puntos=puntos.count(),num_productos=presentaciones.count(),
                   num_ventas=ventas.count(),num_mayoristas=puntos.filter(tipo='Mayorista').count(),
                   num_minoristas=puntos.filter(tipo__in=['Minorista','Tienda','Cafetería']).count(),
                   puede_gestionar_tienda=access(request,{'Bodega'}))
    return render(request,'cadena/area.html',ctx)

@login_required
def nuevo(request,area,tipo):
    if area not in AREAS or tipo not in FORMS or DESTINOS[tipo]!=area:raise Http404('Formulario desconocido')
    if not access(request,ROLE_WRITE[tipo]):return HttpResponseForbidden('No puedes crear registros en esta área.')
    form=FORMS[tipo](request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False)
        if hasattr(obj,'responsable'):obj.responsable=request.user.username
        if tipo=='movimiento':
            with transaction.atomic():
                Material.objects.select_for_update().get(pk=obj.material_id)
                saldo=stock_materiales()[obj.material_id]
                if obj.tipo=='Salida' and obj.cantidad>saldo:
                    form.add_error('cantidad','Stock insuficiente. Disponible: '+str(saldo))
                else:obj.save()
        else:obj.save()
        if not form.errors:
            messages.success(request,'Registro guardado. Puedes consultarlo en el área correspondiente.')
            return redirect('cadena_area',area=area)
    return render(request,'cadena/form.html',{'form':form,'titulo':{'material':'Material','movimiento':'Movimiento de material','receta':'Consumo por kg (receta)','plan':'Plan de producción','punto':'Punto de venta','venta':'Venta en tienda','incidencia':'Incidencia'}[tipo], 'area':area})

@login_required
def mrp(request):
    if not access(request,{'Bodega','Control de calidad'}):return HttpResponseForbidden('Sin autorización')
    materiales=list(Material.objects.all())
    recetas=list(RecetaMaterial.objects.select_related('material'))
    planes=list(PlanProduccion.objects.select_related('lote').order_by('-fecha_programada')[:25])
    saldos=stock_materiales()
    necesidades=defaultdict(lambda:Decimal('0'))
    for plan in planes:
        if plan.estado=='Finalizado':continue
        for r in recetas:
            if plan.receta==r.nombre:necesidades[r.material_id]+=r.cantidad_por_kg*plan.cantidad_objetivo_kg
    resultados=[{'material':m,'stock':saldos[m.id],'necesita':necesidades[m.id],
                 'faltante':max(Decimal('0'),necesidades[m.id]-saldos[m.id]),
                 'reponer':max(Decimal('0'),necesidades[m.id]+m.stock_minimo-saldos[m.id])} for m in materiales]
    return render(request,'cadena/mrp.html',{'resultados':resultados,'planes':planes,'recetas':recetas})

@login_required
def mrp_detalle(request,pk):
    if not access(request,{'Bodega','Control de calidad'}):return HttpResponseForbidden('Sin autorización')
    plan=get_object_or_404(PlanProduccion.objects.select_related('lote'),pk=pk)
    items=[{'r':r,'necesidad':r.cantidad_por_kg*plan.cantidad_objetivo_kg} for r in RecetaMaterial.objects.select_related('material').filter(nombre=plan.receta)]
    return render(request,'cadena/plan.html',{'plan':plan,'items':items})

@login_required
@require_POST
def confirmar_venta(request,pk):
    if not access(request,{'Bodega'}):return HttpResponseForbidden('Sin autorización')
    with transaction.atomic():
        venta=get_object_or_404(VentaTienda.objects.select_for_update(),pk=pk)
        if venta.estado!='Reservado':messages.warning(request,'La venta ya fue procesada.')
        else:
            referencia='TIENDA-'+venta.numero
            if not Pedido.objects.filter(codigo_seguimiento=referencia).exists():
                Pedido.objects.create(cliente=venta.punto_venta.nombre,lote=venta.lote,
                    cantidad_kg=venta.cantidad_kg,destino=venta.punto_venta.direccion or venta.punto_venta.ciudad,
                    codigo_seguimiento=referencia,estado='Pendiente')
            venta.estado='Confirmado';venta.save(update_fields=['estado'])
            messages.success(request,'Venta confirmada; pedido pendiente creado. El inventario se descontará al despachar.')
    return redirect('cadena_area',area='tienda')

@login_required
@require_POST
def revertir_movimiento(request,pk):
    if not access(request,{'Bodega'}):return HttpResponseForbidden('Sin autorización')
    mov=get_object_or_404(MovimientoMaterial,pk=pk)
    with transaction.atomic():
        Material.objects.select_for_update().get(pk=mov.material_id)
        if MovimientoMaterial.objects.filter(referencia=f'REVERSO-{mov.pk}').exists():
            messages.warning(request,'Este movimiento ya tiene reverso.')
        else:
            inverso='Salida' if mov.tipo=='Entrada' else 'Entrada'
            saldo=stock_materiales()[mov.material_id]
            if inverso=='Salida' and saldo<mov.cantidad:messages.error(request,'No se puede revertir: stock insuficiente.')
            else:
                MovimientoMaterial.objects.create(material=mov.material,tipo=inverso,cantidad=mov.cantidad,
                    referencia=f'REVERSO-{mov.pk}',responsable=request.user.username)
                messages.success(request,'Movimiento compensado. Se conservó el registro original.')
    return redirect('cadena_area',area='almacen')

@login_required
def incidencias(request):
    return render(request,'cadena/incidencias.html',{'rows':Incidencia.objects.select_related('lote')[:100]})

@login_required
def catalogo(request):
    q=request.GET.get('q','').strip()[:100]
    metodo=request.GET.get('metodo','')
    rows=Lote.objects.select_related('finca','productor').all()
    if q:rows=rows.filter(Q(codigo__icontains=q)|Q(variedad__icontains=q)|Q(finca__nombre__icontains=q))
    if metodo in dict(Lote.METODOS):rows=rows.filter(metodo_proceso=metodo)
    return render(request,'cadena/catalogo.html',{'lotes':rows[:90],'q':q,'metodo':metodo,'metodos':Lote.METODOS})

@login_required
def experimentos(request):
    return render(request,'cadena/experimentos.html',{'lotes':Lote.objects.count(),
      'movimientos':MovimientoInventario.objects.count()+MovimientoMaterial.objects.count(),
      'pedidos':Pedido.objects.count(),'incidencias':Incidencia.objects.count()})

@login_required
def puntos_tienda(request):
    if not access(request,ROLE_READ['tienda']):return HttpResponseForbidden('Sin autorización')
    puntos=PuntoVenta.objects.all().order_by('tipo','nombre')
    return render(request,'cadena/tienda_puntos.html',{'puntos':puntos,'puede_gestionar':access(request,{'Bodega'})})

@login_required
def presentaciones_tienda(request):
    if not access(request,ROLE_READ['tienda']):return HttpResponseForbidden('Sin autorización')
    q=request.GET.get('q','').strip()[:100]
    productos=PresentacionCafe.objects.select_related('lote','lote__finca').all()
    if q:productos=productos.filter(Q(nombre__icontains=q)|Q(codigo_sku__icontains=q)|Q(lote__codigo__icontains=q))
    return render(request,'cadena/tienda_productos.html',{'productos':productos[:120],'q':q})

@login_required
def qrs_tienda(request):
    if not access(request,ROLE_READ['tienda']):return HttpResponseForbidden('Sin autorización')
    lotes=Lote.objects.select_related('finca','productor').order_by('-id')[:90]
    return render(request,'cadena/tienda_qrs.html',{'lotes':lotes})
