"""Estadísticas comparativas a partir de registros locales, sin predicciones inventadas."""
import calendar
from datetime import date, datetime, time
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from trazabilidad.models import Lote, Pedido, MovimientoInventario
from .models import VentaTienda, ProductoCatalogo


def _autorizado(user):
    return user.is_superuser or user.is_staff or user.groups.filter(name__in=['Producción','Almacén','Distribución','Tienda','Bodega']).exists()


def _meses():
    hoy=timezone.localdate()
    return [date((hoy.year*12+hoy.month-1-i)//12,(hoy.year*12+hoy.month-1-i)%12+1,1) for i in range(5,-1,-1)]


def resumen_series():
    meses=_meses()
    series=[]
    for inicio in meses:
        fin=date((inicio.year*12+inicio.month)//12, (inicio.year*12+inicio.month)%12+1,1)
        ventas=VentaTienda.objects.filter(fecha__date__gte=inicio,fecha__date__lt=fin).exclude(estado='Cancelado')
        pedidos=Pedido.objects.filter(fecha__date__gte=inicio,fecha__date__lt=fin)
        entradas=MovimientoInventario.objects.filter(tipo='Entrada',fecha__date__gte=inicio,fecha__date__lt=fin).aggregate(s=Sum('cantidad_kg'))['s'] or Decimal('0')
        salidas=MovimientoInventario.objects.filter(tipo='Salida',fecha__date__gte=inicio,fecha__date__lt=fin).aggregate(s=Sum('cantidad_kg'))['s'] or Decimal('0')
        series.append({'mes':inicio.strftime('%Y-%m'), 'ventas':ventas.count(),
          'ingresos_usd':round(float(sum((v.total for v in ventas),Decimal('0'))),2),
          'pedidos':pedidos.count(),'lotes':Lote.objects.filter(creado__date__gte=inicio,creado__date__lt=fin).count(),
          'entradas_kg':float(entradas),'salidas_kg':float(salidas)})
    a,b=series[-2:]
    def comparar(campo):
        actual=b[campo]; anterior=a[campo];delta=round(actual-anterior,2)
        return {'actual':actual,'anterior':anterior,'diferencia':delta,
          'variacion_pct':round(delta/anterior*100,1) if anterior else None,
          'tendencia':'sube' if delta>0 else ('baja' if delta<0 else 'igual')}
    return {'periodos':series, 'variacion':{campo:comparar(campo) for campo in ('ventas','ingresos_usd','pedidos','lotes','entradas_kg','salidas_kg')},
      'total_productos_publicados':ProductoCatalogo.objects.filter(activo=True).count(),
      'nota':'Cifras registradas, incluidas transacciones DEMO. Comparación mes actual (parcial) vs mes anterior completo; no es una predicción.'}


@login_required
@require_GET
def panel(request):
    if not _autorizado(request.user):return HttpResponseForbidden('Se requieren permisos operativos para consultar estadísticas internas.')
    data=resumen_series()
    return render(request,'cadena/estadisticas.html',{'data':data})


@login_required
@require_GET
def api_estadisticas(request):
    if not _autorizado(request.user):return JsonResponse({'error':'Sin autorización'},status=403)
    return JsonResponse(resumen_series(),json_dumps_params={'ensure_ascii':False})
