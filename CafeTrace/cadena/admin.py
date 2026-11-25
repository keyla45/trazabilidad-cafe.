from django.contrib import admin
from .models import Material,MovimientoMaterial,RecetaMaterial,PlanProduccion,PuntoVenta,VentaTienda,Incidencia
for m in [Material,MovimientoMaterial,RecetaMaterial,PlanProduccion,PuntoVenta,VentaTienda,Incidencia]:admin.site.register(m)
