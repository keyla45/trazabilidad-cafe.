from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

ROLE_NAMES = ("Productor", "Bodega", "Transportista", "Control de calidad", "Cliente", "Producción", "Almacén", "Distribución", "Tienda")

def roles_for(user):
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return set(ROLE_NAMES)
    return set(user.groups.filter(name__in=ROLE_NAMES).values_list("name", flat=True))

def role_required(*allowed):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            grupos=roles_for(request.user)
            dedicados={'Producción','Almacén','Distribución','Tienda'}
            if not request.user.is_superuser and (not (grupos & dedicados & set(allowed)) if grupos & dedicados else not grupos.intersection(allowed)):
                return HttpResponseForbidden("Tu cuenta no tiene permiso para realizar esta operación.")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator

def roles_context(request):
    roles=roles_for(request.user)
    exclusivos={'Producción','Almacén','Distribución','Tienda'}
    usa_exclusivos=bool(roles & exclusivos)
    if usa_exclusivos:
        accesos={'proveedor':'Productor' in roles,'produccion':'Producción' in roles,
                 'almacen':'Almacén' in roles,'distribucion':'Distribución' in roles,
                 'tienda':'Tienda' in roles}
    else:
        accesos={'proveedor':bool(roles & {'Productor','Bodega','Control de calidad'}),
                 'produccion':bool(roles & {'Bodega','Control de calidad'}),
                 'almacen':'Bodega' in roles,'distribucion':bool(roles & {'Bodega','Transportista'}),
                 'tienda':bool(roles & {'Bodega','Cliente','Transportista'})}
    if request.user.is_authenticated and request.user.is_superuser:
        accesos=dict.fromkeys(accesos,True)
    return {'roles_usuario':roles,'puede_productor':accesos['proveedor'],
      'puede_bodega':accesos['almacen'], 'puede_transporte':accesos['distribucion'],
      'puede_calidad':'Control de calidad' in roles,
      **{'acceso_'+k:v for k,v in accesos.items()}}
