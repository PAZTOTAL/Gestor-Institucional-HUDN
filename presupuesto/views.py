from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from consultas_externas.models import Cpnsolicdp, Psnrbrgas
from core.mixins import AccessControlMixin
from .models import RP  # Keep RP for now as we haven't refactored it yet

class PresupuestoIndexView(AccessControlMixin, TemplateView):
    template_name = 'presupuesto/index.html'
    permission_type = 'view'
    app_label = 'presupuesto'

class ConsultaCDPView(AccessControlMixin, ListView):
    model = Cpnsolicdp
    template_name = 'presupuesto/cdp_list.html'
    context_object_name = 'cdps'
    paginate_by = 50
    permission_type = 'view'
    app_label = 'presupuesto'
    ordering = ['-scdfecdoc']  # Assuming we want to order by date

    def get_queryset(self):
        queryset = super().get_queryset()
        
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        numero = self.request.GET.get('numero')

        # Si no hay filtros, no retornar nada (No desplegar nada mientras no se solicite)
        if not (fecha_desde or fecha_hasta or numero):
            return Cpnsolicdp.objects.none()

        if fecha_desde:
            queryset = queryset.filter(scdfecdoc__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(scdfecdoc__lte=fecha_hasta)
        if numero:
            queryset = queryset.filter(scdconsec__icontains=numero)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cdps = context['cdps']
        
        # Collect all Rubro IDs
        rubro_ids = set(cdp.psnrbrgas for cdp in cdps if cdp.psnrbrgas)
        
        if rubro_ids:
            try:
                rubros = Psnrbrgas.objects.in_bulk(list(rubro_ids))
            except:
                rubros = {} # Fallback if error accessing legacy table
        else:
            rubros = {}
        
        # Attach Rubro info to CDP objects
        for cdp in cdps:
            if cdp.psnrbrgas in rubros:
                rubro = rubros[cdp.psnrbrgas]
                cdp.rubro_code = getattr(rubro, 'sgcfcodrub', 'N/A')
                cdp.rubro_name = getattr(rubro, 'sgcfnomrub', 'N/A')
            else:
                cdp.rubro_code = 'N/A'
                cdp.rubro_name = 'N/A'
                
        return context

class ConsultaRPView(AccessControlMixin, ListView):
    model = RP
    template_name = 'presupuesto/rp_list.html'
    context_object_name = 'rps'
    paginate_by = 50
    permission_type = 'view'
    app_label = 'presupuesto'
    ordering = ['-fecha']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        numero = self.request.GET.get('numero')

        # Si no hay filtros, no retornar nada
        if not (fecha_desde or fecha_hasta or numero):
            return RP.objects.none()

        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        if numero:
            queryset = queryset.filter(rp_numero__icontains=numero)
            
        return queryset

class ConsultaObligacionView(AccessControlMixin, ListView):
    # Placeholder using Cpnsolicdp similarly to CDP until actual 'Obligacion' model is found
    model = Cpnsolicdp 
    template_name = 'presupuesto/obligacion_list.html'
    context_object_name = 'obligaciones'
    paginate_by = 50
    permission_type = 'view'
    app_label = 'presupuesto'
    
    def get_queryset(self):
        # Return empty for now as it's a placeholder, or implement search on mocked model
        # For demonstration, we'll behave like CDP but labeled differently
        # Real implementation requires the correct legacy table.
        
        queryset = super().get_queryset()
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        numero = self.request.GET.get('numero')
        
        if not (fecha_desde or fecha_hasta or numero):
            return Cpnsolicdp.objects.none()

        if fecha_desde:
            queryset = queryset.filter(scdfecdoc__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(scdfecdoc__lte=fecha_hasta)
        if numero:
            queryset = queryset.filter(scdconsec__icontains=numero)
            
        return queryset
