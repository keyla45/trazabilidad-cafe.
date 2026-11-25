"""Pruebas del asistente contextual. No utilizan ninguna API externa."""
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from trazabilidad.models import Productor, Finca, Lote, EventoTrazabilidad, MovimientoInventario


class AsistenteContextualTest(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser('prueba_asistente', 'demo@example.invalid', 'ClavePrueba123!')
        self.client.force_login(self.admin)

    def preguntar(self, q):
        return self.client.get(reverse('cadena_asistente'), {'q': q})

    def test_inventario_no_se_confunde_con_ventas(self):
        r = self.preguntar('¿Cuánto hay en inventario?')
        self.assertEqual(r.status_code, 200)
        self.assertIn('saldo', r.json()['respuesta'].lower())

    def test_stock_consulta_registros(self):
        r = self.preguntar('stock')
        self.assertIn('kg', r.json()['respuesta'])
        self.assertIn('fuente', r.json())

    def test_asistente_guia_fases(self):
        r = self.preguntar('guíame por las cinco áreas')
        self.assertIn('finca', r.json()['respuesta'].lower())
        self.assertIn('distribución', r.json()['respuesta'].lower())

    def test_mrp_consulta_contextual(self):
        r = self.preguntar('¿Qué materiales necesita el MRP?')
        self.assertIn('MRP', r.json()['respuesta'])

    def test_qr_explicacion_celular(self):
        r = self.preguntar('¿Cómo consultar QR desde un teléfono?')
        self.assertIn('127.0.0.1', r.json()['respuesta'])

    def test_consulta_lote_especifico(self):
        productor=Productor.objects.create(nombre='Agricultor de ejemplo')
        finca=Finca.objects.create(nombre='Finca de ensayo', productor=productor)
        lote=Lote.objects.create(codigo='DEMO-ESP-55', productor=productor, finca=finca,
            variedad='Caturra', fecha_cosecha=date(2026, 11, 20), cantidad_kg=Decimal('14'),
            metodo_proceso='Lavado')
        EventoTrazabilidad.objects.create(lote=lote,etapa='Finca',responsable='Demo')
        MovimientoInventario.objects.create(lote=lote,tipo='Entrada',cantidad_kg=Decimal('10'))
        r=self.preguntar('Muéstrame el lote DEMO-ESP-55')
        self.assertEqual(r.status_code,200)
        self.assertIn('Finca de ensayo',r.json()['respuesta'])
        self.assertIn('10.00 kg',r.json()['respuesta'])
        self.assertEqual(r.json()['url'],reverse('detalle_lote',args=[lote.id]))

    def test_codigo_inexistente_no_inventa_datos(self):
        r=self.preguntar('Lote DEMO-ESP-90')
        self.assertIn('No encontré',r.json()['respuesta'])

    def test_guia_y_chat_tienen_pagina(self):
        self.assertEqual(self.client.get(reverse('cadena_herramientas')).status_code,200)
        self.assertContains(self.client.get(reverse('cadena_herramientas')),'RUTA OPERATIVA')

    def test_api_cliente_rechazada(self):
        cliente=get_user_model().objects.create_user('cliente_qa', password='ClaveDemo123!')
        grupo,_=Group.objects.get_or_create(name='Cliente')
        cliente.groups.add(grupo)
        self.client.force_login(cliente)
        self.assertEqual(self.preguntar('inventario').status_code,403)

    def test_api_anonimo_requiere_login(self):
        self.client.logout()
        self.assertEqual(self.preguntar('stock').status_code,302)
