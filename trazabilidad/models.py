from django.db import models
from django.urls import reverse
from django.utils import timezone
import uuid


class Productor(models.Model):
    nombre = models.CharField(max_length=150)
    identificacion = models.CharField(max_length=30, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    comunidad = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Finca(models.Model):
    productor = models.ForeignKey(Productor, on_delete=models.CASCADE, related_name="fincas")
    nombre = models.CharField(max_length=150)
    parroquia = models.CharField(max_length=100, blank=True)
    canton = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, default="Carchi")
    altura_msnm = models.PositiveIntegerField(null=True, blank=True)
    variedad_principal = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.productor.nombre}"


class Lote(models.Model):
    METODOS = [
        ("Lavado", "Lavado"),
        ("Honey", "Honey"),
        ("Natural", "Natural"),
        ("Anaeróbico", "Anaeróbico"),
    ]
    ESTADOS = [
        ("En proceso", "En proceso"),
        ("Aprobado", "Aprobado"),
        ("Rechazado", "Rechazado"),
    ]

    codigo = models.CharField(max_length=30, unique=True, editable=False)
    productor = models.ForeignKey(Productor, on_delete=models.PROTECT, related_name="lotes")
    finca = models.ForeignKey(Finca, on_delete=models.PROTECT, related_name="lotes")
    variedad = models.CharField(max_length=100)
    fecha_cosecha = models.DateField()
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_proceso = models.CharField(max_length=30, choices=METODOS, default="Lavado")
    fecha_ingreso = models.DateField(default=timezone.now)
    humedad = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperatura_secado = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tiempo_fermentacion_horas = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default="En proceso")
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"CAF-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def get_public_url(self):
        return reverse("trazabilidad_publica", args=[self.id])

    def __str__(self):
        return self.codigo


class ControlCalidad(models.Model):
    lote = models.OneToOneField(Lote, on_delete=models.CASCADE, related_name="calidad")
    fecha_catacion = models.DateField(default=timezone.now)
    puntaje = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    defectos = models.PositiveIntegerField(default=0)
    aroma = models.CharField(max_length=200, blank=True)
    sabor = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=30, choices=[
        ("Aprobado", "Aprobado"),
        ("Rechazado", "Rechazado"),
        ("Pendiente", "Pendiente"),
    ], default="Pendiente")
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Calidad {self.lote.codigo}"


class EventoTrazabilidad(models.Model):
    ETAPAS = [
        ("Finca", "Finca"),
        ("Recepción", "Recepción"),
        ("Beneficio", "Beneficio"),
        ("Secado", "Secado"),
        ("Almacenamiento", "Almacenamiento"),
        ("Transporte", "Transporte"),
        ("Venta", "Venta"),
    ]
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name="eventos")
    etapa = models.CharField(max_length=50, choices=ETAPAS)
    fecha = models.DateTimeField(default=timezone.now)
    ubicacion = models.CharField(max_length=150, blank=True)
    responsable = models.CharField(max_length=150, blank=True)
    detalle = models.TextField(blank=True)

    class Meta:
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.lote.codigo} - {self.etapa}"


class RecepcionCereza(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="recepciones")
    fecha = models.DateTimeField(default=timezone.now)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2)
    humedad_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    defectos_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    def __str__(self): return f"Recepción {self.lote.codigo}"

class ProcesoCafe(models.Model):
    ETAPAS = [(s,s) for s in ["Beneficio", "Fermentación", "Secado", "Trillado", "Tueste", "Empaque"]]
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="procesos")
    etapa = models.CharField(max_length=30, choices=ETAPAS)
    inicio = models.DateTimeField(default=timezone.now)
    fin = models.DateTimeField(null=True, blank=True)
    temperatura_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    humedad_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    peso_salida_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    class Meta: ordering = ["-inicio"]
    def __str__(self): return f"{self.etapa}: {self.lote.codigo}"

class LecturaSensor(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="lecturas")
    proceso = models.ForeignKey(ProcesoCafe, on_delete=models.SET_NULL, null=True, blank=True)
    instante = models.DateTimeField(default=timezone.now)
    sensor = models.CharField(max_length=100)
    variable = models.CharField(max_length=30, choices=[(v,v) for v in ["Temperatura", "Humedad", "pH"]])
    valor = models.DecimalField(max_digits=9, decimal_places=3)
    unidad = models.CharField(max_length=20)
    origen = models.CharField(max_length=20, choices=[("Manual","Manual"),("IoT","IoT")],default="Manual")
    class Meta: ordering = ["-instante"]
    def __str__(self): return f"{self.sensor}: {self.valor} {self.unidad}"

class MovimientoInventario(models.Model):
    lote = models.ForeignKey(Lote,on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=15, choices=[("Entrada","Entrada"),("Salida","Salida")])
    cantidad_kg = models.DecimalField(max_digits=10,decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    ubicacion = models.CharField(max_length=120,blank=True)
    referencia = models.CharField(max_length=120,blank=True)
    class Meta: ordering = ["-fecha"]
    def __str__(self): return f"{self.tipo} {self.cantidad_kg} kg {self.lote.codigo}"

class Pedido(models.Model):
    cliente = models.CharField(max_length=150)
    contacto = models.CharField(max_length=150,blank=True)
    lote = models.ForeignKey(Lote,on_delete=models.PROTECT,related_name="pedidos")
    cantidad_kg = models.DecimalField(max_digits=10,decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20,choices=[(s,s) for s in ["Pendiente","Preparado","Despachado","Entregado","Cancelado"]],default="Pendiente")
    destino = models.CharField(max_length=200,blank=True)
    codigo_seguimiento = models.CharField(max_length=80,blank=True)
    destino_cedi = models.BooleanField(default=False)
    def __str__(self): return f"Pedido #{self.pk} {self.cliente}"

class EvaluacionExperimental(models.Model):
    experimento = models.CharField(max_length=2,choices=[("E1","E1 Secado"),("E2","E2 Predicción"),("E3","E3 Origen digital")])
    fecha = models.DateField(default=timezone.now)
    escenario = models.CharField(max_length=20,choices=[("Base","Base"),("Solución","Solución")])
    indicador = models.CharField(max_length=120)
    valor = models.DecimalField(max_digits=12,decimal_places=3)
    unidad = models.CharField(max_length=30)
    evidencia = models.TextField(blank=True)
    def __str__(self): return f"{self.experimento}: {self.indicador}"


class Transporte(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="transportes")
    pedido = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name="transportes")
    transportista = models.CharField(max_length=130)
    placa = models.CharField(max_length=20)
    origen = models.CharField(max_length=150)
    destino = models.CharField(max_length=150)
    fecha_salida = models.DateTimeField(default=timezone.now)
    fecha_llegada = models.DateTimeField(null=True, blank=True)
    temperatura_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    costo_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_salida"]

    def __str__(self):
        return f"{self.placa} | {self.lote.codigo} | {self.destino}"


# Módulo de café especial: registros vinculados al lote y editables por rol.
class VariedadCafe(models.Model):
    nombre = models.CharField(max_length=90, unique=True)
    especie = models.CharField(max_length=40, choices=[('Arábica','Arábica'),('Robusta','Robusta'),('Otra','Otra')], default='Arábica')
    descripcion = models.TextField(blank=True)
    def __str__(self): return self.nombre
    class Meta: ordering = ['nombre']


class EtapaEspecial(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='etapas_especiales')
    orden = models.PositiveSmallIntegerField()
    nombre = models.CharField(max_length=90)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    responsable = models.CharField(max_length=120, blank=True)
    ubicacion = models.CharField(max_length=120, blank=True)
    temperatura_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    humedad_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    peso_entrada_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    peso_salida_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=15, choices=[('Pendiente','Pendiente'),('En curso','En curso'),('Finalizada','Finalizada')], default='Pendiente')
    observaciones = models.TextField(blank=True)
    class Meta:
        ordering = ['orden']
        constraints = [models.UniqueConstraint(fields=['lote','orden'], name='especial_lote_orden_unico')]
    def __str__(self): return f'{self.lote.codigo}: {self.nombre}'


class PerfilEspecial(models.Model):
    lote = models.OneToOneField(Lote, on_delete=models.CASCADE, related_name='perfil_especial')
    variedad_catalogo = models.ForeignKey(VariedadCafe, on_delete=models.SET_NULL, null=True, blank=True)
    catador = models.CharField(max_length=120)
    fecha = models.DateField(default=timezone.localdate)
    protocolo = models.CharField(max_length=120, default='Evaluación interna de referencia')
    puntaje_total = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    aroma = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    sabor = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    acidez = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cuerpo = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    notas_sensoriales = models.CharField(max_length=300, blank=True)
    defectos = models.PositiveIntegerField(default=0)
    decision = models.CharField(max_length=20, choices=[('Pendiente','Pendiente'),('Aprobado','Aprobado'),('Rechazado','Rechazado')], default='Pendiente')
    observaciones = models.TextField(blank=True)
    class Meta: verbose_name = 'Perfil de café especial'
    def __str__(self): return f'Perfil {self.lote.codigo}'


class PresentacionCafe(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='presentaciones_especiales')
    nombre = models.CharField(max_length=100)
    formato = models.CharField(max_length=15, choices=[('Grano','Grano'),('Molido','Molido'),('Verde','Verde')])
    gramos_por_unidad = models.PositiveIntegerField()
    unidades = models.PositiveIntegerField(default=0)
    precio_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    codigo_sku = models.CharField(max_length=60, unique=True)
    es_demo = models.BooleanField(default=False)
    class Meta: ordering = ['lote','nombre']
    def __str__(self): return self.codigo_sku

class GenealogiaLote(models.Model):
    """Relación de transformación entre lotes: permite divisiones y mezclas verificables."""
    lote_origen = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='transformaciones_salida')
    lote_resultante = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='transformaciones_entrada')
    cantidad_origen_kg = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    responsable = models.CharField(max_length=120)
    motivo = models.CharField(max_length=180, blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['lote_origen','lote_resultante'],name='genealogia_par_unico')]
        ordering=['-fecha']
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.lote_origen_id and self.lote_resultante_id:
            if self.lote_origen_id == self.lote_resultante_id:
                raise ValidationError('Un lote no puede ser su propio origen.')
            # Comprobar ciclos completos, no solo el par directo.
            visitados=set()
            pendientes=[self.lote_resultante_id]
            while pendientes:
                actual=pendientes.pop()
                if actual==self.lote_origen_id:
                    raise ValidationError('Esta relación crearía un ciclo de trazabilidad.')
                if actual in visitados: continue
                visitados.add(actual)
                pendientes.extend(GenealogiaLote.objects.filter(lote_origen_id=actual).exclude(pk=self.pk).values_list('lote_resultante_id',flat=True))
        if self.cantidad_origen_kg is not None and self.cantidad_origen_kg <= 0:
            raise ValidationError('La cantidad de origen debe ser positiva.')
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)
    def __str__(self):return f'{self.lote_origen} → {self.lote_resultante}'
