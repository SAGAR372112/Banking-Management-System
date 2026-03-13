"""
Email notification service for transaction events.

Design decisions:
  - Emails are sent via transaction.on_commit() so they only fire
    after the DB transaction successfully commits — never on rollback.
  - Both HTML and plain-text bodies are sent for maximum compatibility.
  - All sending is wrapped in try/except so an email failure never
    breaks the API response.
  - Uses Django's send_mail / EmailMultiAlternatives for portability
    with any EMAIL_BACKEND (SMTP, SendGrid, SES, console, etc.)
"""
import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger("bank")

# Fallback sender — override via settings.DEFAULT_FROM_EMAIL
DEFAULT_FROM = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bankmanagement.com")


def _send(
    subject: str,
    to_email: str,
    text_body: str,
    html_body: str,
) -> None:
    """
    Send a single transactional email.
    Swallows all exceptions so email failures are never surfaced to callers.
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=DEFAULT_FROM,
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("Email sent: subject=%r to=%s", subject, to_email)
    except Exception as exc:
        logger.exception("Failed to send email to %s: %s", to_email, exc)


# ---------------------------------------------------------------------------
# Public notification functions — one per transaction type
# ---------------------------------------------------------------------------

def notify_deposit(
    *,
    recipient_email: str,
    recipient_name: str,
    account_number: str,
    amount: Decimal,
    new_balance: Decimal,
    transaction_id: str,
    reference: str = "",
    timestamp=None,
) -> None:
    """Send deposit confirmation email."""
    timestamp = timestamp or timezone.now()
    context = {
        "recipient_name": recipient_name,
        "account_number": account_number,
        "amount": amount,
        "new_balance": new_balance,
        "transaction_id": transaction_id,
        "reference": reference,
        "timestamp": timestamp,
        "transaction_type": "Deposit",
        "bank_name": getattr(settings, "BANK_NAME", "Bank Management"),
    }
    subject = f"Deposit of {amount} credited to account {account_number}"
    html_body = render_to_string("emails/deposit.html", context)
    text_body = render_to_string("emails/deposit.txt", context)
    _send(subject, recipient_email, text_body, html_body)


def notify_withdrawal(
    *,
    recipient_email: str,
    recipient_name: str,
    account_number: str,
    amount: Decimal,
    new_balance: Decimal,
    transaction_id: str,
    reference: str = "",
    timestamp=None,
) -> None:
    """Send withdrawal confirmation email."""
    timestamp = timestamp or timezone.now()
    context = {
        "recipient_name": recipient_name,
        "account_number": account_number,
        "amount": amount,
        "new_balance": new_balance,
        "transaction_id": transaction_id,
        "reference": reference,
        "timestamp": timestamp,
        "transaction_type": "Withdrawal",
        "bank_name": getattr(settings, "BANK_NAME", "Bank Management"),
    }
    subject = f"Withdrawal of {amount} debited from account {account_number}"
    html_body = render_to_string("emails/withdrawal.html", context)
    text_body = render_to_string("emails/withdrawal.txt", context)
    _send(subject, recipient_email, text_body, html_body)


def notify_transfer_sender(
    *,
    recipient_email: str,
    recipient_name: str,
    from_account_number: str,
    to_account_number: str,
    amount: Decimal,
    new_balance: Decimal,
    transaction_id: str,
    reference: str = "",
    timestamp=None,
) -> None:
    """Send transfer debit confirmation to the sender."""
    timestamp = timestamp or timezone.now()
    context = {
        "recipient_name": recipient_name,
        "from_account_number": from_account_number,
        "to_account_number": to_account_number,
        "amount": amount,
        "new_balance": new_balance,
        "transaction_id": transaction_id,
        "reference": reference,
        "timestamp": timestamp,
        "transaction_type": "Transfer Sent",
        "bank_name": getattr(settings, "BANK_NAME", "Bank Management"),
    }
    subject = f"Transfer of {amount} sent from account {from_account_number}"
    html_body = render_to_string("emails/transfer_sent.html", context)
    text_body = render_to_string("emails/transfer_sent.txt", context)
    _send(subject, recipient_email, text_body, html_body)


def notify_transfer_receiver(
    *,
    recipient_email: str,
    recipient_name: str,
    from_account_number: str,
    to_account_number: str,
    amount: Decimal,
    new_balance: Decimal,
    transaction_id: str,
    reference: str = "",
    timestamp=None,
) -> None:
    """Send transfer credit confirmation to the receiver."""
    timestamp = timestamp or timezone.now()
    context = {
        "recipient_name": recipient_name,
        "from_account_number": from_account_number,
        "to_account_number": to_account_number,
        "amount": amount,
        "new_balance": new_balance,
        "transaction_id": transaction_id,
        "reference": reference,
        "timestamp": timestamp,
        "transaction_type": "Transfer Received",
        "bank_name": getattr(settings, "BANK_NAME", "Bank Management"),
    }
    subject = f"Transfer of {amount} received into account {to_account_number}"
    html_body = render_to_string("emails/transfer_received.html", context)
    text_body = render_to_string("emails/transfer_received.txt", context)
    _send(subject, recipient_email, text_body, html_body)