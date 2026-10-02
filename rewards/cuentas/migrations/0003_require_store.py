from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies = [("cuentas", "0002_perfil_store"), ("stores", "0003_assign_existing_tenants")]
    operations = [migrations.AlterField(model_name="perfil", name="store", field=models.ForeignKey(to="stores.store", on_delete=django.db.models.deletion.PROTECT, related_name="perfiles"))]
