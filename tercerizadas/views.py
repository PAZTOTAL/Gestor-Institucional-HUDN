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
from .permisos import (
    es_admin_global, get_admin_tercerizada, get_empresa_del_admin,
    solo_admin_global, acceso_tercerizada
)


def _ctx_rol(request):
    """Contexto de rol reutilizable para todos los templates."""
    return {
        'es_admin_global': es_admin_global(request.user),
        'empresa_admin': get_empresa_del_admin(request.user),
    }


# ══════════════════════════════════════════════════════════════
# AJAX — Buscar cédula en GENTERCER (Dinámica)
# ══════════════════════════════════════════════════════════════
@login_required
def buscar_en_dinamica(request):
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
    empresa_admin = get_empresa_del_admin(request.user)
    admin_global = es_admin_global(request.user)

    base_qs = ServidorTercerizado.objects
    if not admin_global and empresa_admin:
        base_qs = base_qs.filter(empresa=empresa_admin)

    total_servidores = base_qs.count()
    activos = base_qs.filter(activo_hospital=True).count()
    inactivos = total_servidores - activos
    en_dinamica = base_qs.filter(en_dinamica=True).count()
    sin_dinamica = base_qs.filter(en_dinamica=False).count()

    if admin_global:
        total_empresas = EmpresaTercerizada.objects.filter(activa=True).count()
    else:
        total_empresas = 1 if empresa_admin else 0

    ultimos = base_qs.select_related('empresa').order_by('-fecha_registro')[:5]

    if admin_global:
        por_empresa = (
            EmpresaTercerizada.objects
            .filter(activa=True)
            .annotate(total=Count('servidores'))
            .order_by('-total')[:6]
        )
    else:
        por_empresa = (
            EmpresaTercerizada.objects
            .filter(pk=empresa_admin.pk) if empresa_admin else
            EmpresaTercerizada.objects.none()
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
        **_ctx_rol(request),
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

    # Restringir al admin de tercerizada
    admin_global = es_admin_global(request.user)
    empresa_admin = get_empresa_del_admin(request.user)
    if not admin_global:
        if empresa_admin:
            qs = qs.filter(empresa=empresa_admin)
        else:
            qs = qs.none()

    if q:
        qs = qs.filter(
            Q(numero_documento__icontains=q) |
            Q(primer_nombre__icontains=q) |
            Q(primer_apellido__icontains=q) |
            Q(segundo_apellido__icontains=q)
        )
    if empresa_id and admin_global:
        qs = qs.filter(empresa_id=empresa_id)
    if estado == 'activo':
        qs = qs.filter(activo_hospital=True)
    elif estado == 'inactivo':
        qs = qs.filter(activo_hospital=False)
    if dinamica == 'si':
        qs = qs.filter(en_dinamica=True)
    elif dinamica == 'no':
        qs = qs.filter(en_dinamica=False)

    if admin_global:
        empresas = EmpresaTercerizada.objects.filter(activa=True).order_by('razon_social')
    else:
        empresas = EmpresaTercerizada.objects.filter(pk=empresa_admin.pk) if empresa_admin else EmpresaTercerizada.objects.none()

    context = {
        'servidores': qs,
        'empresas': empresas,
        'q': q,
        'empresa_id': empresa_id,
        'estado': estado,
        'dinamica': dinamica,
        'total': qs.count(),
        'page_title': 'Servidores Tercerizados',
        **_ctx_rol(request),
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

    # Admin tercerizada solo puede ver servidores de su empresa
    admin_global = es_admin_global(request.user)
    if not admin_global:
        empresa_admin = get_empresa_del_admin(request.user)
        if not empresa_admin or servidor.empresa_id != empresa_admin.pk:
            messages.error(request, 'No tiene acceso a este servidor.')
            return redirect('tercerizadas:lista_servidores')

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
        **_ctx_rol(request),
    })


@login_required
def crear_servidor(request):
    admin_global = es_admin_global(request.user)
    empresa_fija = None if admin_global else get_empresa_del_admin(request.user)

    if not admin_global and not empresa_fija:
        messages.error(request, 'No tiene una empresa asignada para registrar servidores.')
        return redirect('tercerizadas:dashboard')

    if request.method == 'POST':
        form = ServidorForm(request.POST, request.FILES, empresa_fija=empresa_fija)
        if form.is_valid():
            servidor = form.save(commit=False)
            servidor.registrado_por = request.user
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
            messages.success(request, f'Servidor {servidor.nombre_completo} registrado correctamente.')
            return redirect('tercerizadas:detalle_servidor', pk=servidor.pk)
    else:
        form = ServidorForm(empresa_fija=empresa_fija)

    return render(request, 'tercerizadas/form_servidor.html', {
        'form': form,
        'titulo': 'Registrar Servidor',
        'page_title': 'Nuevo Servidor',
        **_ctx_rol(request),
    })


@login_required
def editar_servidor(request, pk):
    servidor = get_object_or_404(ServidorTercerizado, pk=pk)

    admin_global = es_admin_global(request.user)
    empresa_fija = None
    if not admin_global:
        empresa_admin = get_empresa_del_admin(request.user)
        if not empresa_admin or servidor.empresa_id != empresa_admin.pk:
            messages.error(request, 'No puede editar servidores de otra empresa.')
            return redirect('tercerizadas:lista_servidores')
        empresa_fija = empresa_admin

    if request.method == 'POST':
        form = ServidorForm(request.POST, request.FILES, instance=servidor, empresa_fija=empresa_fija)
        if form.is_valid():
            srv = form.save(commit=False)
            srv.modificado_por = request.user
            srv.save()
            messages.success(request, 'Servidor actualizado correctamente.')
            return redirect('tercerizadas:detalle_servidor', pk=srv.pk)
    else:
        form = ServidorForm(instance=servidor, empresa_fija=empresa_fija)

    return render(request, 'tercerizadas/form_servidor.html', {
        'form': form,
        'servidor': servidor,
        'titulo': 'Editar Servidor',
        'page_title': f'Editar: {servidor.nombre_completo}',
        **_ctx_rol(request),
    })


# ══════════════════════════════════════════════════════════════
# EMPRESAS
# ══════════════════════════════════════════════════════════════
@login_required
def lista_empresas(request):
    q = request.GET.get('q', '').strip()
    admin_global = es_admin_global(request.user)

    if admin_global:
        qs = EmpresaTercerizada.objects.annotate(
            total_servidores=Count('servidores')
        ).order_by('razon_social')
        if q:
            qs = qs.filter(Q(nit__icontains=q) | Q(razon_social__icontains=q))
    else:
        empresa_admin = get_empresa_del_admin(request.user)
        if not empresa_admin:
            messages.info(request, 'No tiene una empresa tercerizada asignada.')
            return redirect('tercerizadas:dashboard')
        qs = EmpresaTercerizada.objects.filter(pk=empresa_admin.pk).annotate(
            total_servidores=Count('servidores')
        )

    return render(request, 'tercerizadas/lista_empresas.html', {
        'empresas': qs,
        'q': q,
        'page_title': 'Empresas Tercerizadas',
        **_ctx_rol(request),
    })


@login_required
@solo_admin_global
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.registrado_por = request.user
            empresa.save()
            messages.success(request, f'Empresa {empresa.razon_social} registrada.')
            return redirect('tercerizadas:lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'tercerizadas/form_empresa.html', {
        'form': form,
        'titulo': 'Nueva Empresa',
        'page_title': 'Nueva Empresa',
        **_ctx_rol(request),
    })


@login_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(EmpresaTercerizada, pk=pk)
    admin_global = es_admin_global(request.user)

    if not admin_global:
        admin = get_admin_tercerizada(request.user)
        if not admin or admin.empresa_id != empresa.pk:
            messages.error(request, 'Solo puede editar los datos de su propia empresa.')
            return redirect('tercerizadas:lista_empresas')

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa actualizada.')
            return redirect('tercerizadas:lista_empresas')
    else:
        form = EmpresaForm(instance=empresa)

    # Firma del administrador de esta empresa (solo para admin de tercerizada)
    firma_admin = None
    if not admin_global:
        try:
            from consentimientos.models import FirmaFuncionario
            firma_admin = FirmaFuncionario.objects.filter(user=request.user, activo=True).first()
        except Exception:
            pass

    return render(request, 'tercerizadas/form_empresa.html', {
        'form': form,
        'empresa': empresa,
        'titulo': 'Editar Empresa',
        'page_title': f'Editar: {empresa.razon_social}',
        'firma_admin': firma_admin,
        **_ctx_rol(request),
    })


# ══════════════════════════════════════════════════════════════
# FIRMA ELECTRÓNICA DEL ADMINISTRADOR
# ══════════════════════════════════════════════════════════════
@login_required
@acceso_tercerizada
def mi_firma(request):
    from consentimientos.models import FirmaFuncionario
    firma_actual = FirmaFuncionario.objects.filter(user=request.user, activo=True).first()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            firma_b64 = data.get('firma_base64', '').strip()
            if not firma_b64:
                return JsonResponse({'status': 'error', 'message': 'No se recibió la firma.'}, status=400)
            FirmaFuncionario.objects.update_or_create(
                user=request.user,
                defaults={'firma_data': firma_b64, 'activo': True}
            )
            return JsonResponse({'status': 'ok', 'message': 'Firma registrada correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'tercerizadas/mi_firma.html', {
        'firma_actual': firma_actual,
        'page_title': 'Mi Firma Electrónica',
        **_ctx_rol(request),
    })


# ══════════════════════════════════════════════════════════════
# ASIGNACIONES Y AFILIACIONES (inline desde detalle)
# ══════════════════════════════════════════════════════════════
@login_required
def agregar_asignacion(request, servidor_pk):
    servidor = get_object_or_404(ServidorTercerizado, pk=servidor_pk)

    admin_global = es_admin_global(request.user)
    if not admin_global:
        empresa_admin = get_empresa_del_admin(request.user)
        if not empresa_admin or servidor.empresa_id != empresa_admin.pk:
            messages.error(request, 'No puede modificar servidores de otra empresa.')
            return redirect('tercerizadas:lista_servidores')

    if request.method == 'POST':
        form = AsignacionForm(request.POST)
        if form.is_valid():
            asig = form.save(commit=False)
            asig.servidor = servidor
            asig.save()
            messages.success(request, 'Área asignada correctamente.')
            return redirect('tercerizadas:detalle_servidor', pk=servidor_pk)
    else:
        form = AsignacionForm()
    return render(request, 'tercerizadas/form_asignacion.html', {
        'form': form,
        'servidor': servidor,
        'page_title': 'Asignar Área',
        **_ctx_rol(request),
    })


@login_required
def agregar_afiliacion(request, servidor_pk):
    servidor = get_object_or_404(ServidorTercerizado, pk=servidor_pk)

    admin_global = es_admin_global(request.user)
    if not admin_global:
        empresa_admin = get_empresa_del_admin(request.user)
        if not empresa_admin or servidor.empresa_id != empresa_admin.pk:
            messages.error(request, 'No puede modificar servidores de otra empresa.')
            return redirect('tercerizadas:lista_servidores')

    if request.method == 'POST':
        form = AfiliacionForm(request.POST, request.FILES)
        if form.is_valid():
            afil = form.save(commit=False)
            afil.servidor = servidor
            afil.save()
            messages.success(request, 'Afiliación registrada.')
            return redirect('tercerizadas:detalle_servidor', pk=servidor_pk)
    else:
        form = AfiliacionForm()
    return render(request, 'tercerizadas/form_afiliacion.html', {
        'form': form,
        'servidor': servidor,
        'page_title': 'Registrar Afiliación',
        **_ctx_rol(request),
    })
