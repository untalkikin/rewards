from django.db import models

from django.contrib.auth.models import User
from django_userforeignkey.models.fields import UserForeignKey

class ModelClass(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    creado_por = UserForeignKey(auto_user_add=True, on_delete=models.CASCADE)
    actualizado_por = UserForeignKey(auto_user=True, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.nombre