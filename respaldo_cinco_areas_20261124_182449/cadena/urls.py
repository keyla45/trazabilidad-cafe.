from django.urls import path
from . import views, innovacion, empresa_views
urlpatterns=[
 path('empresa/',empresa_views.empresa,name='cadena_empresa_demo'),
 path('empresa/area/<slug:area>/',empresa_views.empresa_area,name='cadena_empresa_area'),
 path('herramientas/',innovacion.centro,name='cadena_herramientas'),
 path('api/resumen/',innovacion.api_resumen,name='cadena_api_resumen'),
 path('api/lote/<str:codigo>/',innovacion.api_trazabilidad,name='cadena_api_lote'),
 path('api/asistente/',innovacion.asistente,name='cadena_asistente'),
 path('',views.inicio,name='inicio'),
 path('areas/<slug:area>/',views.area,name='cadena_area'),
 path('areas/<slug:area>/nuevo/<slug:tipo>/',views.nuevo,name='cadena_nuevo'),
 path('mrp/',views.mrp,name='cadena_mrp'),
 path('mrp/plan/<int:pk>/',views.mrp_detalle,name='cadena_mrp_detalle'),
 path('almacen/movimiento/<int:pk>/revertir/',views.revertir_movimiento,name='cadena_revertir'),
 path('tienda/venta/<int:pk>/confirmar/',views.confirmar_venta,name='cadena_confirmar_venta'),
 path('incidencias/',views.incidencias,name='cadena_incidencias'),
 path('catalogo/',views.catalogo,name='cadena_catalogo'),
 path('experimentos/',views.experimentos,name='cadena_experimentos'),
 path('tienda/puntos/',views.puntos_tienda,name='cadena_puntos'),
 path('tienda/productos/',views.presentaciones_tienda,name='cadena_presentaciones'),
 path('tienda/qr/',views.qrs_tienda,name='cadena_qrs'),
]
