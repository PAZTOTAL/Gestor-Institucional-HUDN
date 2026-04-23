import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    EmpresaTercerizada, ContratoTercerizado, ActividadTercerizado,
    ServidorTercerizado, AsignacionOrganigrama, AfiliacionSeguridad
)
from .forms import (
    EmpresaForm, ContratoForm, ActividadForm,
    ServidorForm, AsignacionForm, AfiliacionForm
)


# ══════════════════════════════════════════════════════════════
# AJAX — Buscar cédula en GENTERCER (Dinámica)
# ══════════════════════════════════════════════════════════════
@login_required
def buscar_en_dinamica(request):
    """Endpoint AJAX: busca un número de documento en GENTERCER."""
    num_doc = request.GET.get('documento', '').strip()
    if not num_doc:
        return JsonResponse({'encontrado': False, 'error': 'Número vacío'})
    try:
        from consultas_externas.models import Gentercer
        tercero = Gentercer.objects.using('readonly').filter(
            ternumdoc=num_doc
        ).first()
        if tercero:
            return JsonResponse({
                'encontrado': True,
                'primer_nombre': (tercero.terprinom or '').strip().title(),
                'segundo_nombre': (tercero.tersegnom or '').strip().title(),
                'primer_apellido': (tercero.terpriape or '').strip().title(),
                'segundo_apellido': (tercero.tersegape or '').strip().title(),
                'tipo_documento': tercero.tertipdoc,
            })
        return JsonResponse({'encontrado': False})
    except Exception as e:
        return JsonResponse({'encontrado': False, 'error': str(e)})


# ══════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPAL
# ══════════════════════════════════════════════════════════════
@login_required
def dashboard(request):
    total_servidores = ServidorTercerizado.objects.count()
    activos = ServidorTercerizado.objects.filter(activo_hospital=True).count()
    inactivos = total_servidores - activos
    total_empresas = EmpresaTercerizada.objects.filter(activa=True).count()
    en_dinamica = ServidorTercerizado.objects.filter(en_dinamica=True).count()
    sin_dinamica = ServidorTercerizado.objects.filter(en_dinamica=False).count()

    # Últimos 5 registrados
    ultimos = ServidorTercerizado.objects.select_related('empresa').order_by('-fecha_registro')[:5]

    # Distribución por empresa
    por_empresa = (
        EmpresaTercerizada.objects
        .filter(activa=True)
        .annotate(total=Count('servidores'))
        .order_by('-total')[:6]
    )

    context = {
        'total_servidores': total_servidores,
        'activos': activos,
        'inactivos': inactivos,
        'total_empresas': total_empresas,
        'en_dinamica': en_dinamica,
        'sin_dinamica': sin_dinamica,
        'ultimos': ultimos,
        'por_empresa': por_empresa,
        'page_title': 'Tercerizadas — Dashboard',
    }
    return render(request, 'tercerizadas/dashboard.html', context)


# ══════════════════════════════════════════════════════════════
# SERVIDORES
# ══════════════════════════════════════════════════════════════
@login_required
def lista_servidores(request):
    q = request.GET.get('q', '').strip()
    empresa_id = request.GET.get('empresa', '')
    estado = request.GET.get('estado', '')
    dinamica = request.GET.get('dinamica', '')

    qs = ServidorTercerizado.objects.select_related(
        'empresa', 'tipo_documento', 'sexo'
    ).order_by('primer_apellido', 'primer_nombre')

    if q:
        qs = qs.filter(
            Q(numero_documento__icontains=q) |
            Q(primer_nombre__icontains=q) |
            Q(primer_apellido__icontains=q) |
            Q(segundo_apellido__icontains=q)
        )
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if estado == 'activo':
        qs = qs.filter(activo_hospital=True)
    elif estado == 'inactivo':
        qs = qs.filter(activo_hospital=False)
    if dinamica == 'si':
        qs = qs.filter(en_dinamica=True)
    elif dinamica == 'no':
        qs = qs.filter(en_dinamica=False)

    empresas = EmpresaTercerizada.objects.filter(activa=True).order_by('razon_social')
    context = {
        'servidores': qs,
        'empresas': empresas,
        'q': q,
        'empresa_id': empresa_id,
        'estado': estado,
        'dinamica': dinamica,
        'total': qs.count(),
        'page_title': 'Servidores Tercerizados',
    }
    return render(request, 'tercerizadas/lista_servidores.html', context)


@login_required
def detalle_servidor(request, pk):
    servidor = get_object_or_404(
        ServidorTercerizado.objects.select_related(
            'empresa', 'contrato', 'tipo_documento', 'grupo_sanguineo',
            'sexo', 'pais_nacimiento', 'departamento_nacimiento', 'municipio_nacimiento',
            'municipio_residencia', 'registrado_por'
        ),
        pk=pk
    )
    asignaciones = servidor.asignaciones.select_related(
        'organigrama_nivel1', 'organigrama_nivel2', 'organigrama_nivel3',
        'organigrama_nivel4', 'actividad', 'verificado_por'
    ).order_by('-fecha_inicio')
    afiliaciones = servidor.afiliaciones.all().order_by('tipo')

    return render(request, 'tercerizadas/detalle_servidor.html', {
        'servidor': servidor,
        'asignaciones': asignaciones,
        'afiliaciones': afiliaciones,
        'page_title': f'{servidor.nombre_completo}',
    })


@login_required
def crear_servidor(request):
    if request.method == 'POST':
        form = ServidorForm(request.POST, request.FILES)
        if form.is_valid():
            servidor = form.save(commit=False)
            servidor.registrado_por = request.user
            # Verificar si existe en Dinámica
            try:
                from consultas_externas.models import Gentercer
                existe = Gentercer.objects.using('readonly').filter(
                    ternumdoc=servidor.numero_documento
                ).exists()
                servidor.en_dinamica = existe
                if existe:
                    servidor.fecha_verificacion_dinamica = timezone.now()
            except Exception:
                servidor.en_dinamica = False
            servidor.save()
            messages.success(request, f'✅ Servidor {servidor.nombre_completo} registrado correctamente.')
            return redirect('tercerizadas:detalle_servidor', pk=servidor.pk)
    else:
        form = ServidorForm()

    return render(request, 'tercerizadas/form_servidor.html', {
        'form': form,
        'titulo': 'Registrar Servidor',
        'page_title': 'Nuevo Servidor',
    })


@login_required
def editar_servidor(request, pk):
    servidor = get_object_or_404(ServidorTercerizado, pk=pk)
    if request.method == 'POST':
        form = ServidorForm(request.POST, request.FILES, instance=servidor)
        if form.is_valid():
            srv = form.save(commit=False)
            srv.modificado_por = request.user
            srv.save()
            messages.success(request, '✅ Servidor actualizado correctamente.')
            return redirect('tercerizadas:detalle_servidor', pk=srv.pk)
    else:
        form = ServidorForm(instance=servidor)

    return render(request, 'tercerizadas/form_servidor.html', {
        'form': form,
        'servidor': servidor,
        'titulo': 'Editar Servidor',
        'page_title': f'Editar: {servidor.nombre_completo}',
    })


# ══════════════════════════════════════════════════════════════
# EMPRESAS
# ══════════════════════════════════════════════════════════════
@login_required
def lista_empresas(request):
    q = request.GET.get('q', '').strip()
    qs = EmpresaTercerizada.objects.annotate(
        total_servidores=Count('servidores')
    ).order_by('razon_social')
    if q:
        qs = qs.filter(Q(nit__icontains=q) | Q(razon_social__icontains=q))

    return render(request, 'tercerizadas/lista_empresas.html', {
        'empresas': qs,
        'q': q,
        'page_title': 'Empresas Tercerizadas',
    })


@login_required
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.registrado_por = request.user
            empresa.save()
            messages.success(request, f'✅ Empresa {empresa.razon_social} registrada.')
            return redirect('tercerizadas:lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'tercerizadas/form_empresa.html', {
        'form': form,
        'titulo': 'Nueva Empresa',
        'page_title': 'Nueva Empresa',
    })


@login_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(EmpresaTercerizada, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Empresa actualizada.')
            return redirect('tercerizadas:lista_empresas')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'tercerizadas/form_empresa.html', {
        'form': form,
        'empresa': empresa,
        'titulo': 'Editar Empresa',
        'page_title': f'Editar: {empresa.razon_social}',
    })


# ══════════════════════════════════════════════════════════════
# ASIGNACIONES Y AFILIACIONES (inline desde detalle)
# ══════════════════════════════════════════════════════════════
@login_required
def agregar_asignacion(request, servidor_pk):
    servidor = get_object_or_404(ServidorTercerizado, pk=servidor_pk)
    if request.method == 'POST':
        form = AsignacionForm(request.POST)
        if form.is_valid():
            asig = form.save(commit=False)
            asig.servidor = servidor
            asig.save()
            messages.success(request, '✅ Área asignada correctamente.')
            return redirect('tercerizadas:detalle_servidor', pk=servidor_pk)
    else:
        form = AsignacionForm()
    return render(request, 'tercerizadas/form_asignacion.html', {
        'form': form,
        'servidor': servidor,
        'page_title': 'Asignar Área',
    })


@login_required
def agregar_afiliacion(request, servidor_pk):
    servidor = get_object_or_404(ServidorTercerizado, pk=servidor_pk)
    if request.method == 'POST':
        form = AfiliacionForm(request.POST, request.FILES)
        if form.is_valid():
            afil = form.save(commit=False)
            afil.servidor = servidor
            afil.save()
            messages.success(request, '✅ Afiliación registrada.')
            return redirect('tercerizadas:detalle_servidor', pk=servidor_pk)
    else:
        form = AfiliacionForm()
    return render(request, 'tercerizadas/form_afiliacion.html', {
        'form': form,
        'servidor': servidor,
        'page_title': 'Registrar Afiliación',
    })
