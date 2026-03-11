"""Initial migration for the accounts app."""
import decimal
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("branches", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BankAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_number", models.CharField(db_index=True, editable=False, max_length=20, unique=True)),
                ("account_type", models.CharField(
                    choices=[("savings", "Savings"), ("current", "Current")],
                    default="savings", max_length=20,
                )),
                ("balance", models.DecimalField(
                    decimal_places=2, default=decimal.Decimal("0.00"),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                )),
                ("status", models.CharField(
                    choices=[("active", "Active"), ("inactive", "Inactive"), ("frozen", "Frozen")],
                    db_index=True, default="active", max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accounts", to="branches.branch")),
                ("customer", models.ForeignKey(
                    db_index=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name="bank_accounts", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"verbose_name": "Bank Account", "verbose_name_plural": "Bank Accounts", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="bankaccount", index=models.Index(fields=["customer", "status"], name="acct_customer_status_idx")),
        migrations.AddIndex(model_name="bankaccount", index=models.Index(fields=["account_number"], name="acct_number_idx")),
    ]
