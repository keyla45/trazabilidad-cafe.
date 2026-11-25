from django import forms
from .models import Lote, Productor


class ProductorForm(forms.ModelForm):
    class Meta:
        model = Productor
        fields = ["nombre", "identificacion", "telefono", "comunidad"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre del productor"}),
            "identificacion": forms.TextInput(attrs={"placeholder": "Cédula"}),
            "telefono": forms.TextInput(attrs={"placeholder": "Teléfono"}),
            "comunidad": forms.TextInput(attrs={"placeholder": "Comunidad"}),
        }


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = [
            "productor", "finca", "variedad", "fecha_cosecha", "cantidad_kg",
            "metodo_proceso", "fecha_ingreso", "humedad",
            "temperatura_secado", "tiempo_fermentacion_horas", "estado", "notas"
        ]
        widgets = {
            "fecha_cosecha": forms.DateInput(attrs={"type": "date"}),
            "fecha_ingreso": forms.DateInput(attrs={"type": "date"}),
            "notas": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        productor = cleaned.get("productor")
        finca = cleaned.get("finca")
        if productor and finca and finca.productor_id != productor.id:
            self.add_error("finca", "La finca seleccionada no pertenece al productor.")
        return cleaned

from .models import Finca, ControlCalidad, EventoTrazabilidad, RecepcionCereza, ProcesoCafe, LecturaSensor, MovimientoInventario, Pedido, EvaluacionExperimental

class FincaForm(forms.ModelForm):
    class Meta:
        model = Finca
        fields = "__all__"

class CalidadForm(forms.ModelForm):
    class Meta:
        model = ControlCalidad
        exclude = ["lote"]

class EventoForm(forms.ModelForm):
    class Meta:
        model = EventoTrazabilidad
        exclude = ["lote"]

class RecepcionForm(forms.ModelForm):
    class Meta:
        model = RecepcionCereza
        fields = ["lote","peso_kg","humedad_pct","defectos_pct","observaciones"]

class ProcesoForm(forms.ModelForm):
    class Meta:
        model = ProcesoCafe
        fields = ["lote","etapa","inicio","fin","temperatura_c","humedad_pct","ph","peso_salida_kg","observaciones"]
        widgets = {"inicio": forms.DateTimeInput(attrs={"type":"datetime-local"},format="%Y-%m-%dT%H:%M"), "fin": forms.DateTimeInput(attrs={"type":"datetime-local"},format="%Y-%m-%dT%H:%M")}

class SensorForm(forms.ModelForm):
    class Meta:
        model = LecturaSensor
        fields = ["lote","proceso","sensor","variable","valor","unidad","origen"]

class InventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ["lote","tipo","cantidad_kg","ubicacion","referencia"]

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente","contacto","lote","cantidad_kg","destino","destino_cedi"]

class ExperimentoForm(forms.ModelForm):
    class Meta:
        model = EvaluacionExperimental
        fields = "__all__"


from .models import Transporte

class TransporteForm(forms.ModelForm):
    class Meta:
        model = Transporte
        fields = ["lote", "pedido", "transportista", "placa", "origen", "destino", "fecha_salida", "fecha_llegada", "temperatura_c", "costo_usd", "observaciones"]
        widgets = {"fecha_salida": forms.DateTimeInput(attrs={"type":"datetime-local"}, format="%Y-%m-%dT%H:%M"), "fecha_llegada": forms.DateTimeInput(attrs={"type":"datetime-local"}, format="%Y-%m-%dT%H:%M")}

    def clean(self):
        data = super().clean()
        pedido = data.get("pedido")
        lote = data.get("lote")
        if pedido and lote and pedido.lote_id != lote.id:
            self.add_error("pedido", "El pedido debe pertenecer al lote seleccionado.")
        if data.get("fecha_salida") and data.get("fecha_llegada") and data["fecha_llegada"] < data["fecha_salida"]:
            self.add_error("fecha_llegada", "La llegada no puede ser anterior a la salida.")
        return data


# Validaciones operativas del capítulo 6: los datos DEMO no equivalen a mediciones reales.
from django.core.exceptions import ValidationError
from decimal import Decimal

class SensorForm(forms.ModelForm):
    class Meta:
        model = LecturaSensor
        fields = ['lote','proceso','sensor','variable','valor','unidad','origen']
    def clean(self):
        d = super().clean()
        variable, unidad, valor = d.get('variable'), d.get('unidad'), d.get('valor')
        unidades = {'Temperatura':'°C','Humedad':'%','pH':'pH'}
        if variable and unidad and unidad != unidades.get(variable):
            self.add_error('unidad', f'Unidad obligatoria para {variable}: {unidades.get(variable)}')
        if variable and valor is not None:
            limites = {'Temperatura':(-30,300),'Humedad':(0,100),'pH':(0,14)}
            a,b=limites[variable]
            if not Decimal(a) <= valor <= Decimal(b): self.add_error('valor','Medición físicamente fuera del rango admitido; verifique instrumento y unidad.')
        if d.get('proceso') and d.get('lote') and d['proceso'].lote_id != d['lote'].pk:
            self.add_error('proceso','El proceso seleccionado pertenece a otro lote.')
        return d

class InventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['lote','tipo','cantidad_kg','ubicacion','referencia']
    def clean_cantidad_kg(self):
        valor = self.cleaned_data['cantidad_kg']
        if valor <= 0: raise ValidationError('La cantidad debe ser mayor que cero.')
        return valor

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente','contacto','lote','cantidad_kg','destino','destino_cedi']
    def clean_cantidad_kg(self):
        valor = self.cleaned_data['cantidad_kg']
        if valor <= 0: raise ValidationError('La cantidad debe ser positiva.')
        return valor

class ExperimentoForm(forms.ModelForm):
    class Meta:
        model = EvaluacionExperimental
        fields = ['experimento','fecha','escenario','indicador','valor','unidad','evidencia']
        widgets = {'fecha': forms.DateInput(attrs={'type':'date'}), 'evidencia':forms.Textarea(attrs={'rows':3})}
    def clean_evidencia(self):
        e = self.cleaned_data.get('evidencia','').strip()
        if not e: raise ValidationError('Registre la fuente o evidencia; no se aceptan cifras sin soporte.')
        return e
