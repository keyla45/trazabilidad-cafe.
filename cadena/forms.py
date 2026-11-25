from django import forms
from .models import Material, MovimientoMaterial, RecetaMaterial, PlanProduccion, PuntoVenta, VentaTienda, Incidencia

class BaseForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values():field.widget.attrs.setdefault('class','mrp-input')
class MaterialForm(BaseForm):
    class Meta:model=Material;fields=['codigo','nombre','unidad','stock_minimo','plazo_reposicion_dias']
class MovimientoForm(BaseForm):
    class Meta:model=MovimientoMaterial;fields=['material','tipo','cantidad','referencia']
class RecetaForm(BaseForm):
    class Meta:model=RecetaMaterial;fields=['nombre','material','cantidad_por_kg']
class PlanForm(BaseForm):
    class Meta:model=PlanProduccion;fields=['lote','receta','cantidad_objetivo_kg','fecha_programada'];widgets={'fecha_programada':forms.DateInput(attrs={'type':'date'})}
class PuntoVentaForm(BaseForm):
    class Meta:model=PuntoVenta;fields=['nombre','tipo','ciudad','direccion']
class VentaForm(BaseForm):
    class Meta:model=VentaTienda;fields=['numero','punto_venta','lote','cantidad_kg','precio_por_kg']
class IncidenciaForm(BaseForm):
    class Meta:model=Incidencia;fields=['area','titulo','descripcion','lote']
