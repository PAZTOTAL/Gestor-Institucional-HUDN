from django.contrib import admin
from django.db import models
from django.apps import apps



APP_LABEL = "BasesGenerales"

def guess_code_field(Model):
    for f in Model._meta.fields:
        if f.name == "codigo":
            return "codigo"
    for f in Model._meta.fields:
        if f.name.lower().startswith("codigo"):
            return f.name
    return Model._meta.pk.name  # fallback: PK

def guess_name_field(Model):
    for f in Model._meta.fields:
        if f.name == "nombre":
            return "nombre"
    for f in Model._meta.fields:
        if f.name.lower().startswith("nombre"):
            return f.name
    return None

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 30
    # NO definas list_display_links ni ordering fijo

    def get_ordering(self, request):
        return (guess_code_field(self.model),)

    def get_list_display(self, request):
        cols = []
        # FKs primero (útil para jerarquías)
        for f in self.model._meta.fields:
            if isinstance(f, models.ForeignKey):
                cols.append(f.name)
        # luego código y nombre si existen
        code = guess_code_field(self.model)
        if code not in cols:
            cols.append(code)
        name = guess_name_field(self.model)
        if name and name not in cols:
            cols.append(name)
        # añade 'descripcion' si existe
        if any(f.name == "descripcion" for f in self.model._meta.fields):
            cols.append("descripcion")
        # si nada, al menos __str__
        return tuple(cols or ("__str__",))

    def get_search_fields(self, request):
        fields = []
        for f in self.model._meta.fields:
            it = f.get_internal_type()
            if it in ("CharField", "TextField", "EmailField"):
                fields.append(f.name)
        return tuple(fields or (self.model._meta.pk.name,))

    def get_readonly_fields(self, request, obj=None):
        # Verificar si el modelo tiene el campo 'usuario' comprobando _meta
        try:
            self.model._meta.get_field("usuario")
            # Si existe, lo agregamos a readonly
            return tuple(self.readonly_fields) + ("usuario",)
        except models.FieldDoesNotExist:
            pass
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        # Asignar usuario actual si el modelo tiene el campo 'usuario'
        try:
            self.model._meta.get_field("usuario")
            # Si no tiene valor, asignamos el usuario actual
            if not getattr(obj, "usuario", None):
                obj.usuario = request.user
        except models.FieldDoesNotExist:
            pass
        super().save_model(request, obj, form, change)

# --- Admin específico para RolesUsuario con Inline de Permisos ---


# --- Registro automático de TODOS los modelos del app ---
for Model in apps.get_app_config(APP_LABEL).get_models():
    try:
        admin.site.register(Model, BaseAdmin)
    except admin.sites.AlreadyRegistered:
        pass


from django.contrib import admin
