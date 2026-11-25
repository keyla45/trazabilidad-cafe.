from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from trazabilidad.models import Productor,Finca,Lote
from cadena.models import MarcaCafe,ProductoCatalogo

class CatalogoMarcasTest(TestCase):
    def setUp(self):
        self.productor=Productor.objects.create(nombre='Productor de prueba')
        self.finca=Finca.objects.create(productor=self.productor,nombre='Finca de prueba')
        self.lote=Lote.objects.create(codigo='PRUEBA-CATALOGO',productor=self.productor,finca=self.finca,variedad='Geisha',fecha_cosecha=timezone.localdate(),cantidad_kg=10,metodo_proceso='Lavado')
        self.marca=MarcaCafe.objects.create(nombre='Marca de prueba')
        self.oferta=ProductoCatalogo.objects.create(marca=self.marca,lote=self.lote,sku='PRUEBA-250',titulo='Geisha lavado',especie='Arábica',gramos=250,precio_usd=Decimal('12.50'))

    def test_catalogo_sin_login(self):
        respuesta=self.client.get(reverse('catalogo_publico'))
        self.assertEqual(respuesta.status_code,200)
        self.assertContains(respuesta,'Marca de prueba')

    def test_filtro_marca_y_especie(self):
        respuesta=self.client.get(reverse('catalogo_publico'),{'marca':str(self.marca.pk),'especie':'Arábica'})
        self.assertContains(respuesta,'Geisha')

    def test_pasaporte_por_producto(self):
        respuesta=self.client.get(reverse('producto_publico',args=[self.oferta.pk]))
        self.assertEqual(respuesta.status_code,200)
        self.assertContains(respuesta,'PRUEBA-250')

    def test_qr_png_del_producto(self):
        respuesta=self.client.get(reverse('producto_qr',args=[self.oferta.pk]))
        self.assertEqual(respuesta.status_code,200)
        self.assertEqual(respuesta['Content-Type'],'image/png')
        self.assertTrue(respuesta.content.startswith(b'\x89PNG'))
