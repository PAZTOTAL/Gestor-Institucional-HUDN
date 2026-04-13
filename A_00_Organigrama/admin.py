from django.contrib import admin
from django.db import models
from django.apps import apps

APP_LABEL = "A_00_Organigrama"

def guess_code_field(Model):
    for f in Model._meta.fields:
        if f.name == "codigo":
            return "codigo"
    for f in Model._meta.fields:
        if f.name.lower().startswith("codigo"):
            return f.name
    return Model._meta.pk.name

def guess_name_field(Model):
    for f in Model._meta.fields:
        if f.name == "nombre":
            return "nombre"
    for f in Model._meta.fields:
        if f.name.lower().startswith("nombre"):
            return f.name
    return None

class OrganigramaBaseAdmin(admin.ModelAdmin):
    list_per_page = 30

    def get_ordering(self, request):
        return (guess_code_field(self.model),)

    def get_list_display(self, request):
        cols = []
        for f in self.model._meta.fields:
            if isinstance(f, models.ForeignKey):
                cols.append(f.name)
        code = guess_code_field(self.model)
        if code not in cols:
            cols.append(code)
        name = guess_name_field(self.model)
        if name and name not in cols:
            cols.append(name)
        if any(f.name == "descripcion" for f in self.model._meta.fields):
            cols.append("descripcion")
        return tuple(cols or ("__str__",))

    def get_search_fields(self, request):
        fields = []
        for f in self.model._meta.fields:
            it = f.get_internal_type()
            if it in ("CharField", "TextField", "EmailField"):
                fields.append(f.name)
        return tuple(fields or (self.model._meta.pk.name,))

    def get_readonly_fields(self, request, obj=None):
        try:
            self.model._meta.get_field("usuario")
            return tuple(self.readonly_fields) + ("usuario",)
        except models.FieldDoesNotExist:
            pass
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        try:
            self.model._meta.get_field("usuario")
            if not getattr(obj, "usuario", None):
                obj.usuario = request.user
        except models.FieldDoesNotExist:
            pass
        super().save_model(request, obj, form, change)

# Registro automático de todos los modelos del app Organigrama
for Model in apps.get_app_config(APP_LABEL).get_models():
    try:
        admin.site.register(Model, OrganigramaBaseAdmin)
    except admin.sites.AlreadyRegistered:
        pass
