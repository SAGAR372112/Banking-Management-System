"""Initial migration for the transactions app."""
import decimal
import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("transaction_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("type", models.CharField(
                    choices=[("deposit", "Deposit"), ("withdrawal", "Withdrawal"), ("transfer", "Transfer")],
                    db_index=True, max_length=20,
                )),
                ("amount", models.DecimalField(
                    decimal_places=2, max_digits=15,
                    validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))],
                )),
                ("reference", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(
                    choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")],
                    db_index=True, default="pending", max_length=20,
                )),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("from_account", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="outgoing_transactions", to="accounts.bankaccount",
                )),
                ("to_account", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="incoming_transactions", to="accounts.bankaccount",
                )),
            ],
            options={"verbose_name": "Transaction", "verbose_name_plural": "Transactions", "ordering": ["-timestamp"]},
        ),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["from_account", "timestamp"], name="txn_from_ts_idx")),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["to_account", "timestamp"], name="txn_to_ts_idx")),
        migrations.AddIndex(model_name="transaction", index=models.Index(fields=["status", "type"], name="txn_status_type_idx")),
    ]
