from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class AccessControlMixin(LoginRequiredMixin):
    permission_type = 'view' # 'view', 'add', 'change', 'delete', 'print'

    def dispatch(self, request, *args, **kwargs):
        # Import inside method to avoid circular imports
        from usuarios.models import PerfilUsuario, PermisoApp, PermisoModelo
        
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
            
        # 1. Admin bypass
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # 2. Perfil Check (using get_or_create to be safe)
        perfil, created = PerfilUsuario.objects.get_or_create(user=request.user)
            
        # 3. App/Model Permission Check
        module_name = kwargs.get('module_name')
        
        # If no module_name in kwargs, check for class attribute
        if not module_name and hasattr(self, 'app_label'):
            module_name = self.app_label
            
        model_name = kwargs.get('model_name')
        
        if module_name:
            # Check App Permission
            app_perm = PermisoApp.objects.filter(user=request.user, app_label=module_name).first()
            if not app_perm or not app_perm.permitido:
                raise PermissionDenied(f"No tienes permiso para acceder al módulo {module_name}.")
            
            # Check Model Permission if specified
            if model_name:
                mod_perm = PermisoModelo.objects.filter(user=request.user, app_label=module_name, model_name=model_name).first()
                # Logic: If app is allowed (passed above), we allow model UNLESS explicitly denied.
                # If mod_perm exists and is False -> DENY
                # If mod_perm is None -> ALLOW (Inherit)
                # If mod_perm is True -> ALLOW
                if mod_perm and not mod_perm.permitido:
                    raise PermissionDenied(f"No tienes permiso para acceder a la tabla {model_name}.")

        # 4. Category / Action Check
        cat = perfil.categoria
        
        if self.permission_type == 'add' and cat not in ['ADMIN', 'EDITOR']:
            raise PermissionDenied("Tu categoría no permite crear registros.")
        elif self.permission_type == 'change' and cat not in ['ADMIN', 'EDITOR']:
            raise PermissionDenied("Tu categoría no permite editar registros.")
        elif self.permission_type == 'delete' and cat != 'ADMIN':
            raise PermissionDenied("Solo los Administradores pueden eliminar registros.")
        elif self.permission_type == 'print' and cat not in ['ADMIN', 'EDITOR', 'IMPRESOR']:
            raise PermissionDenied("Tu categoría no permite imprimir reportes.")

        return super().dispatch(request, *args, **kwargs)

from django.db.models import Q

class SearchFilterMixin:
    """Mixin para añadir búsqueda y filtros de cantidad/orden a ListView"""
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '')
        limit = self.request.GET.get('limit', '')
        order = self.request.GET.get('order', 'asc')

        # 1. Búsqueda Genérica
        if query:
            search_query = Q()
            for field in self.model._meta.get_fields():
                if hasattr(field, 'get_internal_type'):
                    internal_type = field.get_internal_type()
                    if internal_type in ['CharField', 'TextField', 'IntegerField', 'AutoField']:
                        search_query |= Q(**{f"{field.name}__icontains": query})
            queryset = queryset.filter(search_query)

        # 2. Orden por PK
        pk_name = self.model._meta.pk.name if hasattr(self.model._meta, 'pk') and self.model._meta.pk else 'id'
        if order == 'desc':
            queryset = queryset.order_by(f'-{pk_name}')
        elif not queryset.ordered:
            queryset = queryset.order_by(pk_name)

        # 3. Límite
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['current_limit'] = self.request.GET.get('limit', '')
        context['current_order'] = self.request.GET.get('order', 'asc')
        if context['current_limit']:
            context['is_paginated'] = False
        return context
