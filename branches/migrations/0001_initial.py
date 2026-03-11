"""Initial migration for the branches app."""
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("branch_code", models.CharField(
                    max_length=20, unique=True,
                    validators=[django.core.validators.RegexValidator(r"^[A-Z0-9]{3,20}$", "Branch code must be 3–20 uppercase alphanumeric characters.")],
                )),
                ("name", models.CharField(max_length=255)),
                ("address", models.TextField()),
                ("manager_name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Branch", "verbose_name_plural": "Branches", "ordering": ["name"]},
        ),
    ]
