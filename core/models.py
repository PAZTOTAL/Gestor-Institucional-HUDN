from django.db import models

class DashboardModule(models.Model):
    CATEGORIES = (
        ('asistencial', 'ASISTENCIAL'),
        ('administrativo', 'ADMINISTRATIVO'),
        ('juridica', 'JURIDICA'),
        ('talento_humano', 'TALENTO HUMANO'),
        ('financiera', 'BIENES Y SERVICIOS - FINANCIERA'),
        ('varios', 'VARIOS'),
        ('consultas', 'CONSULTAS'),
    )

    name = models.CharField(max_length=100, verbose_name="Nombre del Módulo")
    slug = models.SlugField(max_length=100, verbose_name="Slug (Identificador para permisos)")
    description = models.TextField(verbose_name="Descripción Corta")
    url = models.CharField(max_length=255, verbose_name="URL o Ruta (ej: /parto/)")
    category = models.CharField(max_length=20, choices=CATEGORIES, default='asistencial', verbose_name="Categoría")
    icon = models.TextField(null=True, blank=True, verbose_name="Icono (Path SVG)", help_text="Solo la cadena d='...' del path")
    order = models.IntegerField(default=0, verbose_name="Orden de aparición")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Módulo de Inicio"
        verbose_name_plural = "Módulos de Inicio"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"
