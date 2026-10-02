from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies = [("costumers", "0003_costumer_store_alter_costumer_email_and_more"), ("stores", "0003_assign_existing_tenants")]
    operations = [migrations.AlterField(model_name="costumer", name="store", field=models.ForeignKey(to="stores.store", on_delete=django.db.models.deletion.PROTECT, related_name="clientes"))]
