from django.contrib import admin
from .models import Productor, Finca, Lote, ControlCalidad, EventoTrazabilidad


@admin.register(Productor)
class ProductorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "identificacion", "telefono", "comunidad")
    search_fields = ("nombre", "identificacion")


@admin.register(Finca)
class FincaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "productor", "parroquia", "canton", "provincia", "altura_msnm")
    list_filter = ("provincia",)
    search_fields = ("nombre", "productor__nombre")


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "productor", "finca", "variedad", "metodo_proceso", "estado", "humedad")
    list_filter = ("estado", "metodo_proceso")
    search_fields = ("codigo", "productor__nombre", "finca__nombre")
    readonly_fields = ("codigo", "creado")


@admin.register(ControlCalidad)
class ControlCalidadAdmin(admin.ModelAdmin):
    list_display = ("lote", "puntaje", "defectos", "estado", "fecha_catacion")
    list_filter = ("estado",)
    search_fields = ("lote__codigo",)


@admin.register(EventoTrazabilidad)
class EventoTrazabilidadAdmin(admin.ModelAdmin):
    list_display = ("lote", "etapa", "fecha", "ubicacion", "responsable")
    list_filter = ("etapa",)
    search_fields = ("lote__codigo", "responsable")

from .models import RecepcionCereza, ProcesoCafe, LecturaSensor, MovimientoInventario, Pedido, EvaluacionExperimental
for model in [RecepcionCereza,ProcesoCafe,LecturaSensor,MovimientoInventario,Pedido,EvaluacionExperimental]:
    admin.site.register(model)

from .models import Transporte
admin.site.register(Transporte)

from .models import VariedadCafe, EtapaEspecial, PerfilEspecial, PresentacionCafe
@admin.register(VariedadCafe)
class VariedadCafeAdmin(admin.ModelAdmin):
    list_display=('nombre','especie')
    search_fields=('nombre',)
@admin.register(EtapaEspecial)
class EtapaEspecialAdmin(admin.ModelAdmin):
    list_display=('lote','orden','nombre','estado','responsable')
    list_filter=('estado','nombre')
@admin.register(PerfilEspecial)
class PerfilEspecialAdmin(admin.ModelAdmin):
    list_display=('lote','catador','puntaje_total','decision')
    list_filter=('decision',)
@admin.register(PresentacionCafe)
class PresentacionCafeAdmin(admin.ModelAdmin):
    list_display=('codigo_sku','lote','formato','gramos_por_unidad','unidades')

from .models import GenealogiaLote
@admin.register(GenealogiaLote)
class GenealogiaLoteAdmin(admin.ModelAdmin):
    list_display=('lote_origen','lote_resultante','cantidad_origen_kg','fecha','responsable')
    search_fields=('lote_origen__codigo','lote_resultante__codigo')
    autocomplete_fields=('lote_origen','lote_resultante')
