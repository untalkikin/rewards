from django.core.exceptions import PermissionDenied

def staff_store(request):
    perfil = getattr(request.user, "perfil", None)
    if not perfil or not perfil.activo or not perfil.store_id:
        raise PermissionDenied("Tu perfil necesita un negocio activo asignado.")
    if perfil.sucursal_id and (not perfil.sucursal.activa or perfil.sucursal.store_id != perfil.store_id):
        raise PermissionDenied("La sucursal no corresponde al negocio o está inactiva.")
    return perfil.store

def current_store(request):
    if request.user.is_authenticated:
        try:
            return staff_store(request)
        except PermissionDenied:
            return None
    from costumers.session_auth import get_current_costumer
    customer = get_current_costumer(request)
    return customer.store if customer else None
