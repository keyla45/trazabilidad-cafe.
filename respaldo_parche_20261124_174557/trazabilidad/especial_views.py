from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg, Count
from django.urls import reverse
from .models import Lote, EtapaEspecial, PerfilEspecial, PresentacionCafe, VariedadCafe, EventoTrazabilidad
from .especial_flujos import FLUJOS
from .especial_forms import MetodoEspecialForm, EtapaEspecialForm, PerfilEspecialForm, PresentacionCafeForm
from .permissions import role_required

@login_required
def catalogo(request):
    lotes=Lote.objects.select_related('finca','productor').all()
    metodo=request.GET.get('metodo','')
    if metodo in FLUJOS:lotes=lotes.filter(metodo_proceso=metodo)
    conteos = {row['metodo_proceso']: row['n'] for row in Lote.objects.values('metodo_proceso').annotate(n=Count('id'))}
    categorias = [{'nombre': nombre, 'cantidad': conteos.get(nombre, 0)} for nombre in FLUJOS]
    return render(request,'especial/catalogo.html',{'lotes':lotes[:200], 'metodos':FLUJOS.keys(), 'categorias':categorias,'metodo':metodo,'total':lotes.count(), 'perfiles':PerfilEspecial.objects.count(), 'presentaciones':PresentacionCafe.objects.count(),'variedades':VariedadCafe.objects.all()})

@login_required
def detalle(request,lote_id):
    lote=get_object_or_404(Lote.objects.select_related('productor','finca'),pk=lote_id)
    perfil=PerfilEspecial.objects.filter(lote=lote).first()
    etapas=list(lote.etapas_especiales.all())
    plantilla=FLUJOS.get(lote.metodo_proceso,FLUJOS['Lavado'])
    # La plantilla se muestra sin crear registros de procesos que no hayan ocurrido.
    mapa={e.orden:e for e in etapas}
    flujo=[{'orden':i,'nombre':nombre,'registro':mapa.get(i), 'tipo':'Inspección' if ('recepción' in nombre.lower() or 'catación' in nombre.lower() or 'clasificación' in nombre.lower()) else 'Operación'} for i,nombre in enumerate(plantilla,1)]
    completadas=sum(e.estado=='Finalizada' for e in etapas)
    presentaciones=list(lote.presentaciones_especiales.all())
    return render(request,'especial/detalle.html',{'lote':lote,'flujo':flujo,'perfil':perfil,'presentaciones':presentaciones,'completadas':completadas,'total_etapas':len(plantilla),'avance':round(100*completadas/len(plantilla)) if plantilla else 0,'metodos_disponibles':FLUJOS.keys(),'eventos':EventoTrazabilidad.objects.filter(lote=lote).order_by('-fecha')[:12], 'variedades':VariedadCafe.objects.all()[:12]})

@role_required('Bodega','Producción','Control de calidad')
def metodo(request,lote_id):
    lote=get_object_or_404(Lote,pk=lote_id)
    if request.method=='POST':
        form=MetodoEspecialForm(request.POST,instance=lote)
        if form.is_valid():
            if lote.etapas_especiales.exists():
                messages.error(request,'Hay etapas registradas. No se puede cambiar el método sin una revisión del proceso.')
            else:
                form.save();messages.success(request,'Método actualizado.')
            return redirect('especial_detalle',lote_id=lote.pk)
    else:form=MetodoEspecialForm(instance=lote)
    return render(request,'especial/form.html',{'form':form,'titulo':'Método de beneficio','lote':lote})

@role_required('Bodega','Producción')
def registrar_etapa(request,lote_id,orden):
    lote=get_object_or_404(Lote,pk=lote_id)
    etapas=FLUJOS.get(lote.metodo_proceso)
    if etapas is None or not 1<=orden<=len(etapas):
        from django.http import Http404
        raise Http404('Etapa inexistente')
    obj=EtapaEspecial.objects.filter(lote=lote,orden=orden).first()
    era_finalizada=bool(obj and obj.estado=='Finalizada')
    if request.method=='POST':
        form=EtapaEspecialForm(request.POST,instance=obj)
        if form.is_valid():
            registro=form.save(commit=False)
            registro.lote=lote;registro.orden=orden;registro.nombre=etapas[orden-1]
            registro.save()
            if registro.estado=='Finalizada' and not era_finalizada:
                EventoTrazabilidad.objects.create(lote=lote,etapa='Beneficio',responsable=registro.responsable,ubicacion=registro.ubicacion,detalle='Café especial: '+registro.nombre)
            messages.success(request,'Etapa guardada.');return redirect('especial_detalle',lote_id=lote.pk)
    else:form=EtapaEspecialForm(instance=obj)
    return render(request,'especial/form.html',{'form':form,'titulo':f'Etapa {orden}: {etapas[orden-1]}','lote':lote})

@role_required('Control de calidad')
def catacion(request,lote_id):
    lote=get_object_or_404(Lote,pk=lote_id)
    obj=PerfilEspecial.objects.filter(lote=lote).first()
    if request.method=='POST':
        form=PerfilEspecialForm(request.POST,instance=obj)
        if form.is_valid():
            perfil=form.save(commit=False);perfil.lote=lote;perfil.save()
            # El puntaje NO se calcula sumando cinco atributos; requiere protocolo válido.
            messages.success(request,'Catación guardada.');return redirect('especial_detalle',lote_id=lote.pk)
    else:form=PerfilEspecialForm(instance=obj)
    return render(request,'especial/form.html',{'form':form,'titulo':'Ficha de catación y calidad','lote':lote})

@role_required('Bodega','Producción')
def presentacion(request,lote_id):
    lote=get_object_or_404(Lote,pk=lote_id)
    if request.method=='POST':
        form=PresentacionCafeForm(request.POST)
        if form.is_valid():
            p=form.save(commit=False);p.lote=lote;p.save()
            messages.success(request,'Presentación guardada.');return redirect('especial_detalle',lote_id=lote.pk)
    else:form=PresentacionCafeForm()
    return render(request,'especial/form.html',{'form':form,'titulo':'Nueva presentación comercial','lote':lote})
