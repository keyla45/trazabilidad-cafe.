from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

class EmpresaCincoAreasTest(TestCase):
    def setUp(self):
        U=get_user_model()
        self.admin=U.objects.create_superuser('demo_admin','demo@ejemplo.invalid','clave-super-segura-123')
        self.operario=U.objects.create_user('demo_operario',password='otra-clave-segura-123')
    def test_empresa_no_permite_anonimos(self):
        self.assertEqual(self.client.get(reverse('cadena_empresa_demo')).status_code,302)
    def test_areas_empresa_solo_admin(self):
        self.client.force_login(self.operario)
        self.assertEqual(self.client.get(reverse('cadena_empresa_area',args=['proveedor'])).status_code,403)
    def test_cinco_areas_renderizan_con_admin(self):
        self.client.force_login(self.admin)
        for area in ('proveedor','produccion','almacen','distribucion','tienda'):
            with self.subTest(area=area):
                r=self.client.get(reverse('cadena_empresa_area',args=[area]))
                self.assertEqual(r.status_code,200)
                self.assertContains(r,'SIMULACIÓN ACADÉMICA')
    def test_area_inexistente_404(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('cadena_empresa_area',args=['desconocida'])).status_code,404)
