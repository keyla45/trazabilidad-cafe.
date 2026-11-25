from django.urls import path
from . import views
urlpatterns=[
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
