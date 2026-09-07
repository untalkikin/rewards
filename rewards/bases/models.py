from django.db import models
from django_userforeignkey.models.fields import UserForeignKey


class ModelClass(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    creado_por = UserForeignKey(
        auto_user_add=True,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_creados"
    )

    actualizado_por = UserForeignKey(
        auto_user=True,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_actualizados"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.nombre