from django.db import migrations

def assign_tenants(apps, schema_editor):
    alias = schema_editor.connection.alias
    Store = apps.get_model("stores", "Store")
    Customer = apps.get_model("costumers", "Costumer")
    Profile = apps.get_model("cuentas", "Perfil")
    stores = list(Store.objects.using(alias).values_list("pk", flat=True))
    # Never guess data ownership in a pre-existing multi-business database.
    if Customer.objects.using(alias).filter(store__isnull=True).exists() and len(stores) != 1:
        raise RuntimeError("Asigna store_id a los clientes existentes antes de migrar: no existe un único negocio inequívoco.")
    if len(stores) == 1:
        Customer.objects.using(alias).filter(store__isnull=True).update(store_id=stores[0])
    for profile in Profile.objects.using(alias).filter(store__isnull=True).select_related("sucursal"):
        if profile.sucursal_id:
            profile.store_id = profile.sucursal.store_id
        elif len(stores) == 1:
            profile.store_id = stores[0]
        else:
            raise RuntimeError("Asigna store_id a los dueños sin sucursal antes de migrar.")
        profile.save(using=alias, update_fields=["store"])

class Migration(migrations.Migration):
    dependencies = [
        ("stores", "0002_alter_store_options"),
        ("costumers", "0003_costumer_store_alter_costumer_email_and_more"),
        ("cuentas", "0002_perfil_store"),
    ]
    operations = [migrations.RunPython(assign_tenants, migrations.RunPython.noop)]
