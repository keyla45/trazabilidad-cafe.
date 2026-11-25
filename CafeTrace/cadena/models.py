from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from trazabilidad.models import Lote

class Material(models.Model):
    codigo=models.CharField(max_length=30,unique=True)
    nombre=models.CharField(max_length=140)
    unidad=models.CharField(max_length=15,choices=[('kg','kg'),('unidad','unidad'),('litro','litro')],default='unidad')
    stock_minimo=models.DecimalField(max_digits=12,decimal_places=3,default=0)
    plazo_reposicion_dias=models.PositiveIntegerField(default=3)
    es_demo=models.BooleanField(default=False)
    def __str__(self):return self.nombre

class MovimientoMaterial(models.Model):
    material=models.ForeignKey(Material,on_delete=models.PROTECT,related_name='movimientos')
    tipo=models.CharField(max_length=12,choices=[('Entrada','Entrada'),('Salida','Salida')])
    cantidad=models.DecimalField(max_digits=12,decimal_places=3)
    fecha=models.DateTimeField(default=timezone.now)
    referencia=models.CharField(max_length=120)
    responsable=models.CharField(max_length=120,blank=True)
    def clean(self):
        if self.cantidad is None or self.cantidad<=0:raise ValidationError({'cantidad':'Debe ser positiva.'})
    def save(self,*args,**kwargs):self.full_clean();super().save(*args,**kwargs)

class RecetaMaterial(models.Model):
    nombre=models.CharField(max_length=140)
    material=models.ForeignKey(Material,on_delete=models.PROTECT)
    cantidad_por_kg=models.DecimalField(max_digits=12,decimal_places=4)
    def clean(self):
        if self.cantidad_por_kg is None or self.cantidad_por_kg<=0:raise ValidationError('El consumo unitario debe ser positivo.')
    def __str__(self):return f'{self.nombre} / {self.material}'

class PlanProduccion(models.Model):
    lote=models.ForeignKey(Lote,on_delete=models.PROTECT,related_name='planes_mrp')
    receta=models.CharField(max_length=140,default='Empaque café')
    cantidad_objetivo_kg=models.DecimalField(max_digits=12,decimal_places=3)
    fecha_programada=models.DateField(default=timezone.localdate)
    estado=models.CharField(max_length=20,choices=[('Planificado','Planificado'),('En proceso','En proceso'),('Finalizado','Finalizado')],default='Planificado')
    responsable=models.CharField(max_length=120,blank=True)
    es_demo=models.BooleanField(default=False)
    def clean(self):
        if self.cantidad_objetivo_kg is None or self.cantidad_objetivo_kg<=0:raise ValidationError('La cantidad debe ser positiva.')
    def __str__(self):return f'MRP {self.lote.codigo} ({self.cantidad_objetivo_kg} kg)'

class PuntoVenta(models.Model):
    nombre=models.CharField(max_length=150)
    tipo=models.CharField(max_length=20,choices=[('Tienda','Tienda'),('Cafetería','Cafetería'),('Mayorista','Mayorista'),('Minorista','Minorista')])
    ciudad=models.CharField(max_length=100,blank=True)
    direccion=models.CharField(max_length=200,blank=True)
    es_demo=models.BooleanField(default=False)
    def __str__(self):return self.nombre

class VentaTienda(models.Model):
    numero=models.CharField(max_length=40,unique=True)
    punto_venta=models.ForeignKey(PuntoVenta,on_delete=models.PROTECT,related_name='ventas')
    lote=models.ForeignKey(Lote,on_delete=models.PROTECT,related_name='ventas_tienda')
    cantidad_kg=models.DecimalField(max_digits=12,decimal_places=3)
    precio_por_kg=models.DecimalField(max_digits=12,decimal_places=2)
    fecha=models.DateTimeField(default=timezone.now)
    estado=models.CharField(max_length=15,choices=[('Reservado','Reservado'),('Confirmado','Confirmado'),('Cancelado','Cancelado')],default='Reservado')
    es_demo=models.BooleanField(default=False)
    def clean(self):
        if self.cantidad_kg is None or self.cantidad_kg<=0:raise ValidationError('Cantidad positiva requerida.')
        if self.precio_por_kg is None or self.precio_por_kg<0:raise ValidationError('El precio no puede ser negativo.')
    @property
    def total(self):return self.cantidad_kg*self.precio_por_kg
    def __str__(self):return self.numero

class Incidencia(models.Model):
    area=models.CharField(max_length=25,choices=[(x,x) for x in ['Proveedor','Producción','Almacén','Distribución','Tienda']])
    titulo=models.CharField(max_length=180)
    descripcion=models.TextField()
    lote=models.ForeignKey(Lote,on_delete=models.SET_NULL,null=True,blank=True)
    estado=models.CharField(max_length=15,choices=[('Abierta','Abierta'),('Resuelta','Resuelta')],default='Abierta')
    registrada=models.DateTimeField(default=timezone.now)
    responsable=models.CharField(max_length=120,blank=True)
    def __str__(self):return self.titulo
