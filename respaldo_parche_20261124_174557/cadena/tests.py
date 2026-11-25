from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Material,MovimientoMaterial,RecetaMaterial
from .views import stock_materiales

class CadenaBasicaTest(TestCase):
    def test_materiales_y_stock(self):
        mat=Material.objects.create(codigo='T-1',nombre='Bolsa',unidad='unidad',stock_minimo=3)
        MovimientoMaterial.objects.create(material=mat,tipo='Entrada',cantidad=Decimal('10'),referencia='test')
        MovimientoMaterial.objects.create(material=mat,tipo='Salida',cantidad=Decimal('4'),referencia='test-s')
        self.assertEqual(stock_materiales()[mat.pk],Decimal('6'))
    def test_acceso_protegido(self):
        res=self.client.get(reverse('cadena_area',kwargs={'area':'almacen'}))
        self.assertIn(res.status_code,[301,302])
    def test_superuser_dashboard(self):
        usuario=get_user_model().objects.create_superuser('admin_prueba','admin@ejemplo.com','ClavePrueba123!')
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse('inicio')).status_code,200)
        self.assertEqual(self.client.get(reverse('cadena_mrp')).status_code,200)

class HerramientasDigitalesTest(TestCase):
    def setUp(self):
        self.admin=get_user_model().objects.create_superuser('admin_test','admin@test.local','ClaveSegura123!')

    def test_api_protegida_de_anonimos(self):
        self.assertEqual(self.client.get(reverse('cadena_api_resumen')).status_code,302)

    def test_api_resumen_datos(self):
        self.client.force_login(self.admin)
        response=self.client.get(reverse('cadena_api_resumen'))
        self.assertEqual(response.status_code,200)
        self.assertIn('metricas',response.json())
        self.assertEqual(response.json()['metricas']['lotes'],0)

    def test_asistente_guiado_consulta_inventario(self):
        self.client.force_login(self.admin)
        response=self.client.get(reverse('cadena_asistente'),{'q':'¿Hay inventario?'})
        self.assertEqual(response.status_code,200)
        self.assertIn('saldo',response.json()['respuesta'])

    def test_centro_de_herramientas(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('cadena_herramientas')).status_code,200)

    def test_cliente_no_accede_metricas_privadas(self):
        from django.contrib.auth.models import Group
        usuario=get_user_model().objects.create_user('cliente_prueba',password='ClaveSegura123!')
        grupo,_=Group.objects.get_or_create(name='Cliente')
        usuario.groups.add(grupo)
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse('cadena_api_resumen')).status_code,403)
        self.assertEqual(self.client.get(reverse('cadena_herramientas')).status_code,403)

    def test_lote_inexistente_no_expone_datos(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('cadena_api_lote',args=['NO-EXISTE'])).status_code,404)

    def test_redireccion_por_area_dedicada(self):
        from django.contrib.auth.models import Group
        usuario=get_user_model().objects.create_user('operario_prueba',password='ClaveSegura123!')
        for nombre in ['Bodega','Producción']:
            grupo,_=Group.objects.get_or_create(name=nombre)
            usuario.groups.add(grupo)
        self.client.force_login(usuario)
        self.assertRedirects(self.client.get(reverse('inicio')),reverse('cadena_area',args=['produccion']))
        self.assertEqual(self.client.get(reverse('cadena_area',args=['proveedor'])).status_code,403)


class RevisionOperativaRolesTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group
        self.usuario = get_user_model().objects.create_user('prod_operativo', password='ClaveSegura123!')
        self.usuario.groups.add(Group.objects.get_or_create(name='Producción')[0])
        self.client.force_login(self.usuario)

    def test_area_produccion_si_y_almacen_no(self):
        self.assertEqual(self.client.get(reverse('cadena_area', args=['produccion'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('cadena_area', args=['almacen'])).status_code, 403)

    def test_permite_abrir_formulario_plan_mrp(self):
        self.assertEqual(self.client.get(reverse('cadena_nuevo', args=['produccion','plan'])).status_code, 200)

    def test_no_permite_registrar_material_de_almacen(self):
        self.assertEqual(self.client.get(reverse('cadena_nuevo', args=['almacen','material'])).status_code, 403)

    def test_cliente_no_consulta_lotes_internos(self):
        from django.contrib.auth.models import Group
        self.usuario.groups.clear()
        self.usuario.groups.add(Group.objects.get_or_create(name='Cliente')[0])
        self.assertEqual(self.client.get(reverse('api_lotes')).status_code, 403)

    def test_produccion_puede_abrir_procesos(self):
        self.assertEqual(self.client.get(reverse('modulo', args=['procesos'])).status_code, 200)
