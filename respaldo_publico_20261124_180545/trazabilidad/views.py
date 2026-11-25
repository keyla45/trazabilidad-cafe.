from django.contrib.auth.decorators import login_required
from .permissions import role_required, roles_for
from io import BytesIO
import qrcode
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
import csv
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import LoteForm, ProductorForm
from .models import ControlCalidad, EventoTrazabilidad, Finca, Lote, Productor


@login_required
def inicio(request):
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    from datetime import timedelta
    from decimal import Decimal

    total = Lote.objects.count()
    aprobados = Lote.objects.filter(estado="Aprobado").count()
    rechazados = Lote.objects.filter(estado="Rechazado").count()
    pendientes = Lote.objects.filter(estado="En proceso").count()
    productores = Productor.objects.count()
    fincas = Finca.objects.count()
    pedidos_abiertos = Pedido.objects.filter(estado__in=["Pendiente", "Preparado", "Despachado"]).count()
    transportes = Transporte.objects.count()
    controles = ControlCalidad.objects.count()
    lecturas = LecturaSensor.objects.count()
    humedad_riesgo = Lote.objects.filter(humedad__gt=Decimal("12.0")).count()
    calidad_riesgo = ControlCalidad.objects.filter(puntaje__lt=80).count()
    demora_riesgo = Pedido.objects.filter(estado__in=["Pendiente", "Preparado", "Despachado"], fecha__lt=timezone.now()-timedelta(days=3)).count()
    alerta_total = humedad_riesgo + calidad_riesgo + demora_riesgo
    historial = list(Lote.objects.annotate(mes=TruncMonth("creado")).values("mes").annotate(total=Count("id")).order_by("mes"))[-6:]
    maximo = max([h["total"] for h in historial], default=1)
    meses = [{"nombre": h["mes"].strftime("%m/%Y"), "cantidad": h["total"], "altura": round(h["total"] / maximo * 100)} for h in historial]
    porcentaje_aprobado = round(aprobados / total * 100) if total else 0
    porcentaje_pendiente = round(pendientes / total * 100) if total else 0
    porcentaje_rechazado = max(0, 100-porcentaje_aprobado-porcentaje_pendiente) if total else 0
    stock = MovimientoInventario.objects.aggregate(entradas=Sum("cantidad_kg", filter=Q(tipo="Entrada")), salidas=Sum("cantidad_kg", filter=Q(tipo="Salida")))
    inventario_kg = (stock["entradas"] or 0) - (stock["salidas"] or 0)
    contexto = {
        "total_lotes": total, "aprobados": aprobados, "rechazados": rechazados,
        "pendientes": pendientes, "productores": productores, "fincas": fincas,
        "pedidos_pendientes": pedidos_abiertos, "transportes_total": transportes,
        "controles_total": controles, "lecturas_total": lecturas,
        "alertas_total": alerta_total, "puntaje_medio": ControlCalidad.objects.aggregate(valor=Avg("puntaje"))["valor"],
        "inventario_kg": inventario_kg, "ultimos": Lote.objects.select_related("productor", "finca")[:6],
        "ultimos_pedidos": Pedido.objects.select_related("lote").order_by("-fecha")[:4],
        "historial": meses, "porcentaje_aprobado": porcentaje_aprobado,
        "porcentaje_pendiente": porcentaje_pendiente, "porcentaje_rechazado": porcentaje_rechazado,
        "porcentaje_avance": round(controles / total * 100) if total else 0,
        "nav_alertas": alerta_total,
    }
    return render(request, "inicio.html", contexto)


@login_required
def lista_lotes(request):
    lotes = Lote.objects.select_related("productor", "finca").all()
    q = request.GET.get("q", "").strip()[:100]
    estado = request.GET.get("estado", "")
    productor = request.GET.get("productor", "")
    if q:
        lotes = lotes.filter(Q(codigo__icontains=q) | Q(variedad__icontains=q) | Q(finca__nombre__icontains=q) | Q(productor__nombre__icontains=q))
    if estado in dict(Lote.ESTADOS):
        lotes = lotes.filter(estado=estado)
    if productor.isdigit():
        lotes = lotes.filter(productor_id=int(productor))
    if request.GET.get("exportar") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="cafetrace_lotes.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["Codigo", "Productor", "Finca", "Variedad", "Cosecha", "Cantidad kg", "Humedad %", "Estado"])
        for lote in lotes:
            writer.writerow([lote.codigo, lote.productor.nombre, lote.finca.nombre, lote.variedad, lote.fecha_cosecha, lote.cantidad_kg, lote.humedad, lote.estado])
        return response
    return render(request, "lotes/lista.html", {"lotes": lotes[:300], "q":q, "estado_actual":estado, "productor_actual":productor, "productores": Productor.objects.all(), "estados":Lote.ESTADOS})


@role_required('Productor')
def crear_lote(request):
    if request.method == "POST":
        form = LoteForm(request.POST)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.estado = "En proceso"
            lote.save()
            EventoTrazabilidad.objects.create(
                lote=lote,
                etapa="Finca",
                ubicacion=lote.finca.nombre,
                responsable=lote.productor.nombre,
                detalle="Creación del lote y registro de origen."
            )
            messages.success(request, f"Lote {lote.codigo} creado correctamente.")
            return redirect("detalle_lote", lote_id=lote.id)
    else:
        form = LoteForm()
    return render(request, "lotes/form.html", {"form": form})


@login_required
def detalle_lote(request, lote_id):
    lote = get_object_or_404(
        Lote.objects.select_related("productor", "finca"), id=lote_id
    )
    calidad = ControlCalidad.objects.filter(lote=lote).first()
    eventos = lote.eventos.all()
    return render(request, "lotes/detalle.html", {
        "lote": lote, "calidad": calidad, "eventos": eventos
    })


def qr_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    # Usa la URL externa declarada para que el QR no apunte a localhost.
    # Por seguridad solo se aceptan bases http(s); no deriva dominios de parámetros del usuario.
    from urllib.parse import urlsplit
    base = getattr(settings, "CAFETRACE_PUBLIC_BASE_URL", "").strip().rstrip("/")
    partes = urlsplit(base) if base else None
    ruta = reverse("cafe_publico", args=[lote.id])
    if partes and partes.scheme in ("http", "https") and partes.netloc and not partes.username and not partes.password:
        url = base + ruta
    else:
        url = request.build_absolute_uri(ruta)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def trazabilidad_publica(request, lote_id):
    """Compatibilidad con los QR impresos anteriormente: misma ficha pública moderna."""
    from cadena.publico_views import cafe_publico
    return cafe_publico(request, lote_id)


@login_required
def lista_productores(request):
    productores = Productor.objects.all()
    return render(request, "productores/lista.html", {"productores": productores})


@role_required('Productor')
def crear_productor(request):
    if request.method == "POST":
        form = ProductorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Productor registrado correctamente.")
            return redirect("lista_productores")
    else:
        form = ProductorForm()
    return render(request, "productores/form.html", {"form": form})


@login_required
def lista_fincas(request):
    fincas = Finca.objects.select_related("productor").all()
    return render(request, "fincas/lista.html", {"fincas": fincas})


@login_required
def lista_calidad(request):
    registros = ControlCalidad.objects.select_related("lote").all()
    return render(request, "calidad/lista.html", {"registros": registros})


# Extensión del capítulo 6: formularios operativos y registro de evidencias.
from django.db.models import Sum, Count, Avg
from django.db import transaction
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from .forms import FincaForm, CalidadForm, EventoForm, RecepcionForm, ProcesoForm, SensorForm, InventarioForm, PedidoForm, ExperimentoForm, TransporteForm
from .models import RecepcionCereza, ProcesoCafe, LecturaSensor, MovimientoInventario, Pedido, EvaluacionExperimental, Transporte

MODULE_EDITORS = {
 "recepciones": {"Bodega", "Productor"}, "procesos": {"Bodega", "Producción", "Productor"}, "sensores": {"Bodega", "Producción"},
 "inventario": {"Bodega", "Almacén"}, "pedidos": {"Bodega", "Distribución"}, "experimentos": {"Control de calidad"}, "transportes": {"Bodega", "Distribución", "Transportista"},
}

MODULOS = {
 "recepciones": (RecepcionCereza, RecepcionForm, "Recepción de café"),
 "procesos": (ProcesoCafe, ProcesoForm, "Procesos de producción"),
 "sensores": (LecturaSensor, SensorForm, "Lecturas y monitoreo"),
 "inventario": (MovimientoInventario, InventarioForm, "Movimientos de inventario"),
 "pedidos": (Pedido, PedidoForm, "Pedidos y distribución"),
 "experimentos": (EvaluacionExperimental, ExperimentoForm, "Validación experimental"),
 "transportes": (Transporte, TransporteForm, "Transporte y entregas"),
}

@login_required
def modulo(request, nombre):
    if nombre not in MODULOS: raise Http404()
    lectores = {"recepciones":{"Bodega","Control de calidad","Productor"},"procesos":{"Bodega","Control de calidad","Producción","Productor"},"sensores":{"Bodega","Control de calidad","Producción"},"inventario":{"Bodega","Almacén"},"pedidos":{"Bodega","Transportista","Distribución"},"experimentos":{"Control de calidad"},"transportes":{"Bodega","Transportista","Distribución"}}
    if not request.user.is_superuser and not roles_for(request.user).intersection(lectores[nombre]):
        return HttpResponseForbidden("Sin autorización para consultar este módulo.")
    modelo, form_class, titulo = MODULOS[nombre]
    rows = modelo.objects.all()[:200]
    return render(request, "modulos/lista.html", {"rows":rows,"nombre":nombre,"titulo":titulo,"puede_crear":bool(roles_for(request.user).intersection(MODULE_EDITORS[nombre]))})

from django.http import Http404

@login_required
def modulo_nuevo(request, nombre):
    if nombre not in MODULOS: raise Http404()
    if not request.user.is_superuser and not roles_for(request.user).intersection(MODULE_EDITORS[nombre]):
        return HttpResponseForbidden("No tienes permisos para registrar información en este módulo.")
    modelo, form_class, titulo = MODULOS[nombre]
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if nombre == "inventario" and obj.tipo == "Salida":
            with transaction.atomic():
                Lote.objects.select_for_update().get(pk=obj.lote_id)
                entradas = MovimientoInventario.objects.select_for_update().filter(lote=obj.lote, tipo="Entrada").aggregate(s=Sum("cantidad_kg"))["s"] or 0
                salidas = MovimientoInventario.objects.select_for_update().filter(lote=obj.lote, tipo="Salida").aggregate(s=Sum("cantidad_kg"))["s"] or 0
                if obj.cantidad_kg > entradas - salidas:
                    form.add_error("cantidad_kg", "Existencias insuficientes para registrar la salida.")
                else: obj.save()
        else: obj.save()
        if not form.errors:
            if hasattr(obj,"lote") and nombre in ["recepciones","procesos","inventario","transportes"]:
                EventoTrazabilidad.objects.create(lote=obj.lote, responsable=request.user.get_username(), etapa={"recepciones":"Recepción","procesos":("Secado" if obj.etapa=="Secado" else "Beneficio"),"inventario":"Almacenamiento","transportes":"Transporte"}[nombre], detalle=f"Registro digital: {obj}")
            if nombre == "transportes" and obj.pedido_id:
                EventoTrazabilidad.objects.create(lote=obj.pedido.lote, responsable=request.user.get_username(), etapa="Transporte", detalle=f"Transporte registrado: {obj}")
            messages.success(request,"Registro guardado.")
            return redirect("modulo",nombre=nombre)
    return render(request,"modulos/form.html",{"form":form,"titulo":titulo,"nombre":nombre})

@role_required('Productor')
def crear_finca(request):
    form=FincaForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        form.save();messages.success(request,"Finca guardada.");return redirect("lista_fincas")
    return render(request,"modulos/form.html",{"form":form,"titulo":"Registrar finca","nombre":"fincas"})

@role_required('Control de calidad')
def editar_calidad(request,lote_id):
    lote=get_object_or_404(Lote,pk=lote_id)
    calidad=ControlCalidad.objects.filter(lote=lote).first()
    form=CalidadForm(request.POST or None,instance=calidad)
    if request.method=="POST" and form.is_valid():
        registro=form.save(commit=False);registro.lote=lote;registro.save()
        lote.estado=registro.estado if registro.estado in ("Aprobado","Rechazado") else "En proceso"
        lote.save(update_fields=["estado"])
        EventoTrazabilidad.objects.create(lote=lote,etapa="Beneficio",responsable=request.user.get_username(),detalle=f"Control de calidad: {registro.estado}; puntaje: {registro.puntaje}")
        messages.success(request,"Catación actualizada.");return redirect("detalle_lote",lote_id=lote.id)
    return render(request,"modulos/form.html",{"form":form,"titulo":f"Catación {lote.codigo}","nombre":"calidad"})

@role_required("Bodega", "Transportista", "Control de calidad", "Producción", "Distribución")
def crear_evento(request,lote_id):
    lote=get_object_or_404(Lote,pk=lote_id)
    form=EventoForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        evento=form.save(commit=False);evento.lote=lote;evento.responsable=request.user.get_username();evento.save();return redirect("detalle_lote",lote_id=lote.id)
    return render(request,"modulos/form.html",{"form":form,"titulo":f"Evento del lote {lote.codigo}","nombre":"eventos"})

@role_required('Bodega','Control de calidad','Producción','Almacén','Distribución')
def indicadores(request):
    procesos=ProcesoCafe.objects.values("etapa").annotate(total=Count("id"),temperatura=Avg("temperatura_c"))
    resumen={"lotes":Lote.objects.count(),"recepciones":RecepcionCereza.objects.count(),"procesos":ProcesoCafe.objects.count(),"lecturas":LecturaSensor.objects.count(),"pedidos":Pedido.objects.count(),"promedio_catacion":ControlCalidad.objects.aggregate(v=Avg("puntaje"))["v"]}
    return render(request,"modulos/indicadores.html",{"resumen":resumen,"procesos":procesos})

@role_required('Bodega','Control de calidad','Producción','Almacén','Distribución','Productor')
def api_lotes(request):
    return JsonResponse({"results":[{"codigo":x.codigo,"id":x.id,"estado":x.estado,"origen":x.finca.nombre,"variedad":x.variedad,"humedad":str(x.humedad) if x.humedad is not None else None} for x in Lote.objects.select_related("finca")[:200]]})

@role_required('Bodega','Distribución')
def api_cedi(request,pedido_id):
    pedido=get_object_or_404(Pedido,pk=pedido_id,destino_cedi=True)
    if pedido.estado not in ("Preparado","Despachado","Entregado"):
        return JsonResponse({"error":"El pedido todavía no está preparado para despacho"},status=409)
    return JsonResponse({"origen":"Planta de Café UPEC","id_despacho":pedido.id,"lote":pedido.lote.codigo,"producto":"Café","cantidad_kg":str(pedido.cantidad_kg),"destino":"CEDI UPEC","estado":pedido.estado,"fecha":pedido.fecha.isoformat()})

@login_required
@require_POST
@role_required('Bodega', 'Transportista','Distribución')
def actualizar_pedido(request,pedido_id):
    pedido=get_object_or_404(Pedido,pk=pedido_id)
    estado=request.POST.get("estado")
    estados=["Pendiente","Preparado","Despachado","Entregado","Cancelado"]
    if estado not in estados:return JsonResponse({"error":"Estado inválido"},status=400)
    if "Transportista" in roles_for(request.user) and estado != "Entregado":
        return HttpResponseForbidden("El transportista únicamente puede confirmar la entrega.")
    if "Transportista" in roles_for(request.user) and pedido.estado != "Despachado":
        return JsonResponse({"error":"Solo pueden entregarse pedidos despachados"},status=409)
    if estado=="Preparado" and pedido.estado!="Pendiente":
        return JsonResponse({"error":"Transición no permitida"},status=409)
    if estado=="Entregado" and pedido.estado!="Despachado":
        return JsonResponse({"error":"Primero debe despacharse"},status=409)
    if pedido.estado in ("Entregado","Cancelado"):
        return JsonResponse({"error":"Pedido finalizado"},status=409)
    # Nunca se descuenta dos veces el mismo pedido.
    if estado == "Despachado" and pedido.estado != "Despachado":
        if pedido.estado != "Preparado":return JsonResponse({"error":"Primero debe prepararse el pedido"},status=409)
        with transaction.atomic():
            pedido=Pedido.objects.select_for_update().get(pk=pedido.pk)
            Lote.objects.select_for_update().get(pk=pedido.lote_id)
            if pedido.estado != "Preparado": return JsonResponse({"error":"Estado cambiado; recargue el pedido"},status=409)
            entradas=MovimientoInventario.objects.select_for_update().filter(lote=pedido.lote,tipo="Entrada").aggregate(s=Sum("cantidad_kg"))["s"] or 0
            salidas=MovimientoInventario.objects.select_for_update().filter(lote=pedido.lote,tipo="Salida").aggregate(s=Sum("cantidad_kg"))["s"] or 0
            if pedido.cantidad_kg>entradas-salidas:return JsonResponse({"error":"Inventario insuficiente"},status=409)
            MovimientoInventario.objects.create(lote=pedido.lote,tipo="Salida",cantidad_kg=pedido.cantidad_kg,referencia=f"Pedido {pedido.pk}")
            pedido.estado=estado
            pedido.save(update_fields=["estado"])
    if estado != "Despachado":
        pedido.estado=estado;pedido.save(update_fields=["estado"])
    if estado in ("Despachado","Entregado"):
        EventoTrazabilidad.objects.create(lote=pedido.lote,etapa="Transporte" if estado=="Despachado" else "Venta",detalle=f"Pedido {pedido.pk}: {estado}")
    return redirect("modulo",nombre="pedidos")


@login_required
def alertas(request):
    from decimal import Decimal
    from django.utils import timezone
    from datetime import timedelta
    humedad_alta = Lote.objects.filter(humedad__gt=Decimal("12.0")).select_related("finca")
    cataciones_bajas = ControlCalidad.objects.filter(puntaje__lt=80).select_related("lote")[:25]
    lecturas_humedad = LecturaSensor.objects.filter(variable="Humedad",valor__gt=Decimal("12.0")).select_related("lote")[:25]
    pedidos_atrasados = Pedido.objects.filter(estado__in=["Pendiente","Preparado","Despachado"],fecha__lt=timezone.now()-timedelta(days=3)).select_related("lote")
    return render(request,"modulos/alertas.html",{"humedad_alta":humedad_alta,"lecturas_humedad":lecturas_humedad,"pedidos_atrasados":pedidos_atrasados,"cataciones_bajas":cataciones_bajas})

@login_required
def reporte_lote(request, lote_id):
    lote = get_object_or_404(Lote.objects.select_related("productor", "finca"), pk=lote_id)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{lote.codigo}_trazabilidad.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Campo", "Valor"])
    for nombre, valor in [("Lote",lote.codigo),("Productor",lote.productor.nombre),("Finca",lote.finca.nombre),("Variedad",lote.variedad),("Fecha cosecha",lote.fecha_cosecha),("Cantidad kg",lote.cantidad_kg),("Humedad %",lote.humedad),("Estado",lote.estado)]:
        writer.writerow([nombre, valor])
    writer.writerow([])
    writer.writerow(["Etapa", "Fecha", "Ubicacion", "Responsable", "Detalle"])
    for evento in lote.eventos.all():
        writer.writerow([evento.etapa,evento.fecha.isoformat(),evento.ubicacion,evento.responsable,evento.detalle])
    return response


@login_required
def cinco_modulos(request):
    """Centro de operaciones: cinco grandes módulos de la cadena del café."""
    resumen = {
        'origen': Productor.objects.count(),
        'produccion': ProcesoCafe.objects.count(),
        'especial': ControlCalidad.objects.filter(estado='Aprobado', puntaje__gte=80).count(),
        'distribucion': Pedido.objects.count(),
        'qr': Lote.objects.count(),
    }
    return render(request, 'modulos/cinco.html', {'resumen_modulos': resumen})


@login_required
def cafe_especial(request):
    """Catálogo de microlotes elegibles con su ficha de calidad y QR."""
    lotes = (Lote.objects.select_related('productor', 'finca', 'calidad')
             .filter(estado='Aprobado', calidad__estado='Aprobado', calidad__puntaje__gte=80)
             .order_by('-calidad__puntaje', '-creado'))
    return render(request, 'modulos/especial.html', {
        'lotes': lotes[:200], 'total': lotes.count(),
        'criterio': 'Aprobado y catación desde 80 puntos (umbral ilustrativo configurable en futuras versiones).',
    })
