from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ConsentimientoTemplate, ConsentimientoRegistro
from consultas_externas.models import Genpacien
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class ConsentimientoListView(LoginRequiredMixin, ListView):
    model = ConsentimientoTemplate
    template_name = 'ConsentimientosInformados/list.html'
    context_object_name = 'templates'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['registros_recientes'] = ConsentimientoRegistro.objects.all().order_by('-fecha_firma')[:15]
        return context

class TemplateCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ConsentimientoTemplate
    fields = ['nombre', 'descripcion', 'contenido_html', 'activo']
    template_name = 'ConsentimientosInformados/template_form.html'
    success_url = reverse_lazy('consentimientos:list')

    def test_func(self):
        return self.request.user.is_staff

class TemplateUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ConsentimientoTemplate
    fields = ['nombre', 'descripcion', 'contenido_html', 'activo']
    template_name = 'ConsentimientosInformados/template_form.html'
    success_url = reverse_lazy('consentimientos:list')

    def test_func(self):
        return self.request.user.is_staff

class ConsentimientoCreateView(LoginRequiredMixin, CreateView):
    model = ConsentimientoRegistro
    template_name = 'ConsentimientosInformados/form.html'
    fields = ['template', 'paciente_oid', 'profesional_oid', 'firma_paciente', 'firma_profesional', 'foto_paciente', 'huella_paciente', 'datos_extra']
    success_url = reverse_lazy('consentimientos:list')

    def get_initial(self):
        initial = super().get_initial()
        template_id = self.kwargs.get('template_id')
        if template_id:
            initial['template'] = get_object_or_404(ConsentimientoTemplate, pk=template_id)
        return initial

    def form_valid(self, form):
        # El template viene de initial si se pasa por URL
        if not form.instance.template_id:
            form.instance.template_id = self.kwargs.get('template_id')
        
        response = super().form_valid(form)
        
        # Lógica de Email (Placeholder para el servidor de correo)
        if self.request.POST.get('email_enviar') == 'on':
            email = self.request.POST.get('email_destino')
            if email:
                # Aquí se llamaría a una función para generar PDF y enviar por correo
                # Por ahora marcamos como enviado
                self.object.email_enviado = True
                self.object.email_destino = email
                self.object.save()
        
        return response

class ConsentimientoDetailView(LoginRequiredMixin, DetailView):
    model = ConsentimientoRegistro
    template_name = 'ConsentimientosInformados/detail.html'
    context_object_name = 'registro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Intentar obtener datos del paciente desde el OID
        try:
            context['paciente'] = Genpacien.objects.using('readonly').get(oid=self.object.paciente_oid)
        except Genpacien.DoesNotExist:
            context['paciente'] = None
        return context

def buscar_pacientes(request):
    query = request.GET.get('q', '')
    if len(query) < 3:
        return JsonResponse({'results': []})
    
    # Buscar en la base de datos de solo lectura
    pacientes = Genpacien.objects.using('readonly').filter(
        Q(pacnumdoc__icontains=query) | 
        Q(pacprinom__icontains=query) | 
        Q(pacpriape__icontains=query)
    )[:10]
    
    results = []
    for p in pacientes:
        nombre_completo = f"{p.pacprinom or ''} {p.pacsegnom or ''} {p.pacpriape or ''} {p.pacsegape or ''}".strip()
        results.append({
            'oid': p.oid,
            'doc': p.pacnumdoc,
            'nombre': nombre_completo,
            'text': f"{p.pacnumdoc} - {nombre_completo}"
        })
    
    return JsonResponse({'results': results})
