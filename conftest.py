"""Factory Boy factories for test data generation."""
import factory
from faker import Faker

from branches.models import Branch
from users.models import User
from accounts.models import BankAccount
from transactions.models import Transaction

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")
    role = User.Role.CUSTOMER
    phone = factory.Faker("phone_number")
    address = factory.Faker("address")


class AdminUserFactory(UserFactory):
    """Factory for admin users."""
    role = User.Role.ADMIN
    username = factory.Sequence(lambda n: f"admin_{n}")


class BranchFactory(factory.django.DjangoModelFactory):
    """Factory for bank branches."""

    class Meta:
        model = Branch

    branch_code = factory.Sequence(lambda n: f"BR{n:04d}")
    name = factory.Faker("company")
    address = factory.Faker("address")
    manager_name = factory.Faker("name")


class BankAccountFactory(factory.django.DjangoModelFactory):
    """Factory for bank accounts."""

    class Meta:
        model = BankAccount

    account_type = BankAccount.AccountType.SAVINGS
    balance = factory.Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    status = BankAccount.Status.ACTIVE
    customer = factory.SubFactory(UserFactory)
    branch = factory.SubFactory(BranchFactory)


class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for transactions."""

    class Meta:
        model = Transaction

    type = Transaction.TransactionType.DEPOSIT
    amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    status = Transaction.TransactionStatus.COMPLETED
    to_account = factory.SubFactory(BankAccountFactory)
