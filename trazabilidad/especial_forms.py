from django import forms
from .models import PerfilEspecial, EtapaEspecial, PresentacionCafe, Lote

class MetodoEspecialForm(forms.ModelForm):
    class Meta:
        model=Lote
        fields=['metodo_proceso']

class EtapaEspecialForm(forms.ModelForm):
    class Meta:
        model=EtapaEspecial
        fields=['estado','responsable','ubicacion','fecha_inicio','fecha_fin','temperatura_c','humedad_pct','ph','peso_entrada_kg','peso_salida_kg','observaciones']
        widgets={x:forms.DateTimeInput(attrs={'type':'datetime-local'},format='%Y-%m-%dT%H:%M') for x in ['fecha_inicio','fecha_fin']}
    def clean(self):
        c=super().clean()
        if c.get('fecha_inicio') and c.get('fecha_fin') and c['fecha_fin'] < c['fecha_inicio']:
            self.add_error('fecha_fin','La fecha final no puede ser anterior al inicio.')
        for key in ('humedad_pct',):
            if c.get(key) is not None and not 0 <= c[key] <= 100:self.add_error(key,'Debe estar entre 0 y 100.')
        if c.get('ph') is not None and not 0 <= c['ph'] <= 14:self.add_error('ph','El pH debe estar entre 0 y 14.')
        return c

class PerfilEspecialForm(forms.ModelForm):
    class Meta:
        model=PerfilEspecial
        exclude=['lote']
        widgets={'fecha':forms.DateInput(attrs={'type':'date'}),'observaciones':forms.Textarea(attrs={'rows':3})}
    def clean(self):
        c=super().clean()
        for k in ('aroma','sabor','acidez','cuerpo','balance'):
            if c.get(k) is not None and not 0 <= c[k] <= 10:self.add_error(k,'Escala interna entre 0 y 10.')
        if c.get('puntaje_total') is not None and not 0 <= c['puntaje_total'] <= 100:self.add_error('puntaje_total','Debe estar entre 0 y 100.')
        return c

class PresentacionCafeForm(forms.ModelForm):
    class Meta:
        model=PresentacionCafe
        fields=['nombre','formato','gramos_por_unidad','unidades','precio_usd','codigo_sku']
    def clean_gramos_por_unidad(self):
        n=self.cleaned_data['gramos_por_unidad']
        if n<=0:raise forms.ValidationError('El peso debe ser mayor a cero.')
        return n
