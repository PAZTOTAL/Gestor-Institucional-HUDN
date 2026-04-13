from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
# from empresa.models import Reg03Empresa_Usuario, Reg01Empresa
# 
# @receiver(post_save, sender=User)
# def crear_usuario_empresa(sender, instance, created, **kwargs):
#     if created:
#         try:
#             empresa = Reg01Empresa.objects.first()  # Asigna la empresa por defecto o según lógica tuya
#             Reg03Empresa_Usuario.objects.create(
#                 Empresa=empresa,
#                 user=instance,
#                 tipoUsuario="OPERADOR"  # Rol por defecto al crear
#             )
#         except Exception as e:
#             print(f"[!] Error creando Reg03Empresa_Usuario: {e}")


