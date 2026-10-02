from .access import current_store

def negocio(request):
    return {"negocio": current_store(request)}
