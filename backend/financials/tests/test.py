from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from financials.models import (
    Account,
    Budget,
    ExpenseCategory,
    FinancialTransaction,
    IncomeCategory,
)


BASE_URL = '/api/financials/'


class FinancialAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username='financial-owner', email='financial-owner@example.com', password='pass',
        )
        self.other_user = user_model.objects.create_user(
            username='financial-other', email='financial-other@example.com', password='pass',
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.owner)

    def test_financial_endpoints_require_authentication(self):
        for path in ('accounts/', 'transactions/', 'budgets/', 'dashboard/', 'profit-loss/'):
            response = self.client.get(BASE_URL + path)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, path)

    def test_accounts_are_scoped_and_default_setup_is_exposed(self):
        self.authenticate()

        response = self.client.get(BASE_URL + 'accounts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        self.assertTrue(all(row['is_system'] for row in response.data))
        self.assertIn('account_type_display', response.data[0])

    def test_owner_can_create_expense_and_serializer_builds_ledger_lines(self):
        self.authenticate()
        categories = self.client.get(BASE_URL + 'expense-categories/').data
        feed = next(row for row in categories if row['name'] == 'Feed')

        response = self.client.post(BASE_URL + 'transactions/', {
            'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
            'expense_category': feed['id'],
            'title': 'Feed purchase',
            'quantity': '10.00',
            'unit_price': '100.00',
            'extra_amount': '25.50',
            'transaction_date': '2026-08-03',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '1025.50')
        self.assertEqual(len(response.data['lines']), 2)
        self.assertEqual(response.data['lines'][0]['amount'], '1025.50')

    def test_transaction_rejects_missing_category_and_invalid_amount(self):
        self.authenticate()

        missing_category = self.client.post(BASE_URL + 'transactions/', {
            'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
            'title': 'Missing category',
            'amount': '100.00',
            'transaction_date': '2026-08-03',
        }, format='json')
        invalid_amount = self.client.post(BASE_URL + 'transactions/', {
            'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
            'title': 'Invalid amount',
            'amount': '0.00',
            'transaction_date': '2026-08-03',
        }, format='json')

        self.assertEqual(missing_category.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expense_category', missing_category.data)
        self.assertEqual(invalid_amount.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', invalid_amount.data)

    def test_transactions_are_isolated_between_users(self):
        self.authenticate()
        category = ExpenseCategory.objects.create(owner=self.owner, name='Owner-only')
        FinancialTransaction.objects.create(
            owner=self.owner,
            transaction_type=FinancialTransaction.TransactionType.EXPENSE,
            expense_category=category,
            title='Owner transaction',
            amount=Decimal('50.00'),
            transaction_date=date(2026, 8, 1),
        )
        other_category = ExpenseCategory.objects.create(owner=self.other_user, name='Other-only')
        FinancialTransaction.objects.create(
            owner=self.other_user,
            transaction_type=FinancialTransaction.TransactionType.EXPENSE,
            expense_category=other_category,
            title='Other transaction',
            amount=Decimal('75.00'),
            transaction_date=date(2026, 8, 1),
        )

        response = self.client.get(BASE_URL + 'transactions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row['title'] for row in response.data], ['Owner transaction'])

    def test_dashboard_and_profit_loss_return_calculated_totals(self):
        self.authenticate()
        expense_category = ExpenseCategory.objects.create(owner=self.owner, name='Test expense')
        income_category = IncomeCategory.objects.create(owner=self.owner, name='Test income')
        FinancialTransaction.objects.create(
            owner=self.owner,
            transaction_type=FinancialTransaction.TransactionType.EXPENSE,
            expense_category=expense_category,
            title='Expense', amount=Decimal('300.00'), transaction_date=date.today(),
        )
        FinancialTransaction.objects.create(
            owner=self.owner,
            transaction_type=FinancialTransaction.TransactionType.INCOME,
            income_category=income_category,
            title='Income', amount=Decimal('1000.00'), transaction_date=date.today(),
        )

        dashboard = self.client.get(BASE_URL + 'dashboard/')
        profit_loss = self.client.get(BASE_URL + 'profit-loss/')

        self.assertEqual(dashboard.status_code, status.HTTP_200_OK)
        self.assertEqual(profit_loss.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard.data['summary']['income'], Decimal('1000.00'))
        self.assertEqual(dashboard.data['summary']['expenses'], Decimal('300.00'))
        self.assertEqual(dashboard.data['summary']['profit'], Decimal('700.00'))
        self.assertEqual(profit_loss.data['net_profit'], Decimal('700.00'))

    def test_budget_list_includes_actual_spend_and_remaining_amount(self):
        self.authenticate()
        category = ExpenseCategory.objects.create(owner=self.owner, name='Budget expense')
        Budget.objects.create(
            owner=self.owner,
            expense_category=category,
            name='Monthly feed',
            amount=Decimal('1000.00'),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        FinancialTransaction.objects.create(
            owner=self.owner,
            transaction_type=FinancialTransaction.TransactionType.EXPENSE,
            expense_category=category,
            title='Budget spend', amount=Decimal('250.00'),
            transaction_date=date(2026, 8, 1),
        )

        response = self.client.get(BASE_URL + 'budgets/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['actual_spend'], '250.00')
        self.assertEqual(response.data[0]['remaining'], '750.00')
        self.assertEqual(response.data[0]['used_percent'], 25.0)

    def test_automatic_record_endpoint_creates_idempotent_record(self):
        self.authenticate()
        payload = {
            'source_type': FinancialTransaction.SourceType.HARVEST_SALE,
            'source_id': 44,
            'quantity': '5',
            'unit_price': '400',
        }

        first = self.client.post(BASE_URL + 'automatic-records/', payload, format='json')
        second = self.client.post(BASE_URL + 'automatic-records/', payload, format='json')

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(first.data['amount'], '2000.00')

