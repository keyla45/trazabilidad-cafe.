from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from trazabilidad.models import Productor,Finca,Lote
from .models import MarcaCafe,ProductoCatalogo

class EstadisticasChatTest(TestCase):
    def setUp(self):
        prod=Productor.objects.create(nombre='Finca test')
        finca=Finca.objects.create(productor=prod,nombre='Origen test')
        self.lote=Lote.objects.create(codigo='DEMO-ESP-78',productor=prod,finca=finca,variedad='Geisha',fecha_cosecha=date(2026,11,1),cantidad_kg=10,metodo_proceso='Lavado')
        marca=MarcaCafe.objects.create(nombre='Café Prueba')
        self.o=ProductoCatalogo.objects.create(marca=marca,lote=self.lote,sku='TEST-GEISHA-250',titulo='Geisha',gramos=250,precio_usd=Decimal('9.50'),es_demo=True)
    def test_catalogo_publico_con_chat(self):
        r=self.client.get(reverse('catalogo_publico'))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'pub-chat-form')
    def test_chat_publico_sin_login_precio(self):
        r=self.client.get(reverse('cadena_chat_catalogo'),{'q':'¿Cuánto cuesta Geisha?'})
        self.assertEqual(r.status_code,200)
        self.assertIn('9.50',r.json()['respuesta'])
    def test_chat_publico_no_revela_inventario(self):
        r=self.client.get(reverse('cadena_chat_catalogo'),{'q':'Dime el saldo de inventario interno'})
        self.assertNotIn('saldo documental',r.json()['respuesta'].lower())
    def test_sku_con_qr_abre_en_misma_pestana(self):
        r=self.client.get(reverse('producto_publico',args=[self.o.pk]))
        self.assertEqual(r.status_code,200)
        self.assertNotContains(r,'target="_blank"')
    def test_estadisticas_privadas(self):
        self.assertEqual(self.client.get(reverse('cadena_api_estadisticas')).status_code,302)
        admin=get_user_model().objects.create_superuser('super_qa','x@invalid.test','pass1234')
        self.client.force_login(admin)
        r=self.client.get(reverse('cadena_api_estadisticas'))
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()['periodos']),6)
        self.assertIn('variacion',r.json())
        self.assertEqual(self.client.get(reverse('cadena_estadisticas')).status_code,200)
