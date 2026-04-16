from django.contrib import admin
from .models import DashboardModule

@admin.register(DashboardModule)
class DashboardModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description', 'slug')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
