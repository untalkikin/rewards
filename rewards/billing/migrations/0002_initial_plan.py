from django.db import migrations
def prepare_plan(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.using(schema_editor.connection.alias).get_or_create(nombre="Rewards SaaS", defaults={"descripcion": "Tarjetas digitales, promociones, sucursales y reportes para tu negocio.", "precio": None, "moneda": "MXN", "intervalo_meses": 1})
class Migration(migrations.Migration):
    dependencies = [("billing", "0001_initial")]
    operations = [migrations.RunPython(prepare_plan, migrations.RunPython.noop)]
