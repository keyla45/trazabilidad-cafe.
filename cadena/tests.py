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

class EmpresaSimuladaTest(TestCase):
    def test_empresa_exige_sesion(self):
        self.assertEqual(self.client.get(reverse('cadena_empresa_demo')).status_code,302)

    def test_empresa_dashboard_para_admin(self):
        admin=get_user_model().objects.create_superuser('admin_empresa','admin@empresa.test','ClaveSegura123!')
        self.client.force_login(admin)
        r=self.client.get(reverse('cadena_empresa_demo'))
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'Origen y Taza')

    def test_demo_repetible_y_qr(self):
        from django.core.management import call_command
        from trazabilidad.models import Lote
        from io import StringIO
        call_command('cargar_empresa_demo',stdout=StringIO())
        n=Lote.objects.filter(codigo__startswith='DEMO-ESP-').count()
        self.assertEqual(n,4)
        call_command('cargar_empresa_demo',stdout=StringIO())
        self.assertEqual(Lote.objects.filter(codigo__startswith='DEMO-ESP-').count(),n)
        lote=Lote.objects.get(codigo='DEMO-ESP-01')
        qr=self.client.get(reverse('qr_lote',args=[lote.id]))
        self.assertEqual(qr.status_code,200)
        self.assertEqual(qr['Content-Type'],'image/png')
        pagina=self.client.get(reverse('trazabilidad_publica',args=[lote.id]))
        self.assertEqual(pagina.status_code,200)
        self.assertContains(pagina,'DATOS FICTICIOS')


class CatalogoPublicoQRTest(TestCase):
    def test_catalogo_sin_inicio_de_sesion(self):
        respuesta=self.client.get(reverse('catalogo_publico'))
        self.assertEqual(respuesta.status_code,200)
        self.assertContains(respuesta,'Nuestros cafés')
        self.assertContains(respuesta,'Acceso a administración')

    def test_login_ofrece_catalogo_publico(self):
        respuesta=self.client.get(reverse('login'))
        self.assertEqual(respuesta.status_code,200)
        self.assertContains(respuesta,reverse('catalogo_publico'))

    def test_pasaporte_sin_sesion_y_qr_con_host_de_red(self):
        from django.core.management import call_command
        from django.test import override_settings
        from unittest.mock import patch
        from io import StringIO
        from trazabilidad.models import Lote
        call_command('cargar_empresa_demo',stdout=StringIO())
        lote=Lote.objects.get(codigo='DEMO-ESP-01')
        self.assertEqual(self.client.get(reverse('cafe_publico',args=[lote.id])).status_code,200)
        self.assertContains(self.client.get(reverse('cafe_publico',args=[lote.id])),'PRESENTACIONES COMERCIALES')
        with override_settings(CAFETRACE_PUBLIC_BASE_URL='http://192.168.1.50:8000'):
            with patch('trazabilidad.views.qrcode.QRCode') as qr_class:
                respuesta=self.client.get(reverse('cafe_qr_publico',args=[lote.id]))
                self.assertEqual(respuesta.status_code,200)
                self.assertEqual(respuesta['Content-Type'],'image/png')
                qr_class.return_value.add_data.assert_called_once_with(
                    'http://192.168.1.50:8000'+reverse('cafe_publico',args=[lote.id]))
