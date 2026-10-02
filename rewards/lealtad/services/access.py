from django.core.exceptions import PermissionDenied

def validar_operacion(tarjeta, sucursal, cajero):
    perfil = getattr(cajero, "perfil", None)
    if (not cajero.is_active or not perfil or not perfil.activo or perfil.rol != "CAJERO"
        or perfil.sucursal_id != sucursal.pk or perfil.store_id != sucursal.store_id
        or tarjeta.costumer.store_id != sucursal.store_id or not sucursal.activa or not tarjeta.activa):
        raise PermissionDenied("Operación fuera del negocio o tarjeta/sucursal inactiva.")
