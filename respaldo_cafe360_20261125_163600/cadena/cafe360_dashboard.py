"""Datos del panel Café360. No genera tendencias ni precios artificiales."""
from datetime import date
from django.apps import apps
from django.utils import timezone


def dashboard_context():
    # Cálculos de lectura solamente; no alteran la BD.
    from cadena.models import VentaTienda
    from trazabilidad.models import Pedido
    hoy = timezone.localdate()
    indice = hoy.year * 12 + hoy.month - 1
    meses = [date((indice - i) // 12, (indice - i) % 12 + 1, 1) for i in range(5, -1, -1)]
    periodos = []
    for comienzo in meses:
        fin_indice = comienzo.year * 12 + comienzo.month
        fin = date(fin_indice // 12, fin_indice % 12 + 1, 1)
        ventas = VentaTienda.objects.filter(fecha__date__gte=comienzo, fecha__date__lt=fin).exclude(estado='Cancelado')
        pedidos = Pedido.objects.filter(fecha__date__gte=comienzo, fecha__date__lt=fin)
        periodos.append({'mes': comienzo.strftime('%Y-%m'), 'ventas': ventas.count(), 'pedidos': pedidos.count()})
    def variacion(clave):
        anterior, actual = periodos[-2][clave], periodos[-1][clave]
        diferencia = actual-anterior
        return {'actual': actual, 'anterior': anterior, 'diferencia': diferencia,
                'variacion_pct': round(diferencia*100/anterior, 1) if anterior else None,
                'tendencia': 'sube' if diferencia>0 else 'baja' if diferencia<0 else 'igual'}
    # Los ingresos se agregan para el mes vigente, no se estiman.
    from decimal import Decimal
    inicio=meses[-1]
    importe=sum((v.total for v in VentaTienda.objects.filter(fecha__date__gte=inicio).exclude(estado='Cancelado')),
                Decimal('0'))
    productos=[]
    try:
        modelo=apps.get_model('cadena', 'ProductoCatalogo')
        productos=list(modelo.objects.filter(activo=True).select_related('marca','lote__finca').order_by('marca__nombre','gramos')[:4])
    except (LookupError, Exception) as error:
        # Si la instalación aún no tiene la tabla del catálogo, el panel no debe caerse.
        # Evitar ocultar errores operativos no relacionados con la tabla:
        from django.db.utils import OperationalError, ProgrammingError
        if not isinstance(error, (LookupError, OperationalError, ProgrammingError)):
            raise
    return {'c360_stats': {'periodos': periodos, 'variacion': {
                'ventas': variacion('ventas'), 'pedidos': variacion('pedidos'),
                'ingresos_usd': {'actual': importe}}},
            'c360_productos': productos,
            'c360_max_ventas': max(1,*(r['ventas'] for r in periodos)),
            'c360_max_pedidos': max(1,*(r['pedidos'] for r in periodos))}
