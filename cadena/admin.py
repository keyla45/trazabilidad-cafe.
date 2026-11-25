from django.contrib import admin
from .models import Material,MovimientoMaterial,RecetaMaterial,PlanProduccion,PuntoVenta,VentaTienda,Incidencia
for m in [Material,MovimientoMaterial,RecetaMaterial,PlanProduccion,PuntoVenta,VentaTienda,Incidencia]:admin.site.register(m)

from .models import MarcaCafe, ProductoCatalogo

@admin.register(MarcaCafe)
class MarcaCafeAdmin(admin.ModelAdmin):
    list_display = ('nombre','activa','es_demo')
    search_fields = ('nombre',)

@admin.register(ProductoCatalogo)
class ProductoCatalogoAdmin(admin.ModelAdmin):
    list_display = ('sku','titulo','marca','lote','formato','gramos','precio_usd','unidades','activo','es_demo')
    search_fields = ('sku','titulo','marca__nombre','lote__codigo')
    list_filter = ('marca','especie','formato','categoria','es_demo','activo')
