from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from financials.models import Account, FinancialTransaction, TransactionLine
from financials.services import (
    budget_actual_spend,
    create_automatic_financial_record,
    ensure_default_financial_setup,
    month_bounds,
    sync_transaction_lines,
)


class FinancialServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='financial-service-user',
            email='financial-service@example.com',
            password='StrongPass123!',
        )

    def test_default_setup_is_idempotent_and_creates_expected_accounts(self):
        ensure_default_financial_setup(self.user)
        ensure_default_financial_setup(self.user)

        self.assertEqual(Account.objects.filter(owner=self.user).count(), 10)
        self.assertEqual(self.user.expense_categories.count(), 7)
        self.assertEqual(self.user.income_categories.count(), 2)
        self.assertTrue(Account.objects.get(owner=self.user, name='Cash').is_system)

    def test_automatic_expense_calculates_amount_and_creates_balanced_lines(self):
        record = create_automatic_financial_record(self.user, {
            'source_type': FinancialTransaction.SourceType.FEED_PURCHASE,
            'source_id': 41,
            'quantity': '10',
            'unit_price': '100.00',
            'extra_amount': '25.50',
            'transaction_date': date(2026, 8, 3),
        })

        self.assertEqual(record.amount, Decimal('1025.50'))
        self.assertEqual(record.transaction_type, FinancialTransaction.TransactionType.EXPENSE)
        self.assertEqual(record.expense_category.name, 'Feed')
        self.assertTrue(record.is_automatic)
        self.assertEqual(record.lines.count(), 2)
        self.assertEqual(
            list(record.lines.values_list('entry_type', flat=True)),
            [TransactionLine.EntryType.DEBIT, TransactionLine.EntryType.CREDIT],
        )
        self.assertEqual(sum(line.amount for line in record.lines.all()), Decimal('2051.00'))

    def test_automatic_income_uses_income_category_and_is_idempotent(self):
        payload = {
            'source_type': FinancialTransaction.SourceType.HARVEST_SALE,
            'source_id': 9,
            'quantity': '20',
            'unit_price': '350',
        }

        first = create_automatic_financial_record(self.user, payload)
        second = create_automatic_financial_record(self.user, payload)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(FinancialTransaction.objects.count(), 1)
        self.assertEqual(first.amount, Decimal('7000.00'))
        self.assertEqual(first.income_category.name, 'Harvest Sales')

    def test_unsupported_automatic_source_is_rejected(self):
        with self.assertRaisesMessage(ValueError, 'Unsupported automatic source type.'):
            create_automatic_financial_record(self.user, {'source_type': 'unknown'})

    def test_month_bounds_handles_leap_year(self):
        start, end = month_bounds(date(2028, 2, 12))

        self.assertEqual(start, date(2028, 2, 1))
        self.assertEqual(end, date(2028, 2, 29))

