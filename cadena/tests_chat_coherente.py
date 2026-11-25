"""Pruebas de preguntas naturales, sin servicios de IA externos."""
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from trazabilidad.models import Productor, Finca, Lote
from .models import MarcaCafe, ProductoCatalogo


class ConversacionesCoherentesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        productor = Productor.objects.create(nombre='Productora ejemplo')
        finca = Finca.objects.create(productor=productor, nombre='Finca prueba')
        lote = Lote.objects.create(codigo='DEMO-ESP-991', productor=productor, finca=finca,
            variedad='Geisha', fecha_cosecha=date(2026, 11, 2), cantidad_kg=Decimal('25'),
            metodo_proceso='Lavado')
        marca = MarcaCafe.objects.create(nombre='Café Prueba', es_demo=True)
        ProductoCatalogo.objects.create(marca=marca, lote=lote, sku='PRUEBA-GEISHA-250',
            titulo='Geisha', gramos=250, precio_usd=Decimal('10.50'), es_demo=True)
        cls.admin = get_user_model().objects.create_superuser('asistente_qa', 'qa@example.invalid', 'Pass-1234!')

    def preguntar_publico(self, pregunta):
        return self.client.get(reverse('cadena_chat_catalogo'), {'q': pregunta})

    def preguntar_admin(self, pregunta):
        self.client.force_login(self.admin)
        return self.client.get(reverse('cadena_asistente'), {'q': pregunta})

    def test_publico_aroma_no_responde_con_conteo(self):
        r = self.preguntar_publico('¿Qué café tiene más olor?')
        self.assertEqual(r.status_code, 200)
        respuesta = r.json()['respuesta'].lower()
        self.assertIn('aroma', respuesta)
        self.assertIn('no contiene', respuesta)
        self.assertNotIn('presentaciones activas', respuesta)

    def test_publico_precio_especifico_no_se_rompe(self):
        r = self.preguntar_publico('¿Cuánto cuesta Geisha?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('10.50', r.json()['respuesta'])

    def test_publico_no_inventa_mas_vendido(self):
        r = self.preguntar_publico('¿Cuál es el café más vendido?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('no puedo identificar', r.json()['respuesta'].lower())

    def test_publico_economico_compara_mismo_gramaje(self):
        r = self.preguntar_publico('¿Cuál es el café más barato?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('250 g', r.json()['respuesta'])

    def test_admin_para_que_almacen_no_devuelve_stock(self):
        r = self.preguntar_admin('para que sirve el apartado de almacen')
        self.assertEqual(r.status_code, 200)
        respuesta = r.json()['respuesta'].lower()
        self.assertIn('kardex', respuesta)
        self.assertIn('sirve', respuesta)
        self.assertNotIn('saldo documental de café es', respuesta)

    def test_admin_stock_sigue_consultando_datos(self):
        r = self.preguntar_admin('¿Cuánto stock tenemos?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('saldo documental', r.json()['respuesta'].lower())

    def test_admin_produccion_explicativa(self):
        r = self.preguntar_admin('¿Cómo funciona el módulo de producción?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('transformaciones', r.json()['respuesta'])

    def test_admin_distribucion_explicativa(self):
        r = self.preguntar_admin('¿Para qué sirve distribución?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('entrega', r.json()['respuesta'].lower())
