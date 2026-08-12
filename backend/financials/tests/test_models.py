from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from financials.models import (
    Account,
    Budget,
    ExpenseCategory,
    FinancialTransaction,
    IncomeCategory,
    TransactionLine,
)


class FinancialModelUnitTests(SimpleTestCase):
    def build_account(self, **overrides):
        values = {
            'owner_id': 1,
            'name': 'Cash',
            'account_type': Account.AccountType.ASSET,
        }
        values.update(overrides)
        return Account(**values)

    def build_transaction(self, **overrides):
        values = {
            'owner_id': 1,
            'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
            'expense_category_id': 1,
            'title': 'Feed purchase',
            'amount': Decimal('1200.00'),
            'transaction_date': date(2026, 8, 1),
        }
        values.update(overrides)
        return FinancialTransaction(**values)

    def test_account_clean_rejects_blank_name(self):
        with self.assertRaises(ValidationError) as raised:
            self.build_account(name=' ').clean()

        self.assertEqual(raised.exception.message_dict['name'], ['Account name is required.'])

    def test_transaction_clean_requires_matching_category(self):
        transaction = self.build_transaction(expense_category_id=None)

        with self.assertRaises(ValidationError) as raised:
            transaction.clean()

        self.assertEqual(
            raised.exception.message_dict['expense_category'],
            ['Expense category is required for expense transactions.'],
        )

    def test_expense_transaction_requires_expense_category(self):
        transaction = self.build_transaction(
            expense_category_id=None,
            income_category=IncomeCategory(owner_id=1, name='Sales'),
        )

        with self.assertRaises(ValidationError) as raised:
            transaction.clean()

        self.assertIn('expense_category', raised.exception.message_dict)

    def test_budget_clean_rejects_invalid_amount_and_date_range(self):
        budget = Budget(
            owner_id=1,
            name='Feed budget',
            amount=Decimal('0.00'),
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 1),
        )

        with self.assertRaises(ValidationError) as raised:
            budget.clean()

        self.assertEqual(set(raised.exception.message_dict), {'amount', 'end_date'})

    def test_transaction_line_clean_rejects_other_owner_and_non_positive_amount(self):
        transaction = self.build_transaction()
        account = self.build_account(owner_id=2)
        line = TransactionLine(
            transaction=transaction,
            account=account,
            entry_type=TransactionLine.EntryType.DEBIT,
            amount=Decimal('0.00'),
        )

        with self.assertRaises(ValidationError) as raised:
            line.clean()

        self.assertEqual(set(raised.exception.message_dict), {'account'})

    def test_category_clean_validates_account_owner_and_type(self):
        account = self.build_account(owner_id=2, account_type=Account.AccountType.INCOME)
        category = ExpenseCategory(owner_id=1, name='Feed', account=account)

        with self.assertRaises(ValidationError) as raised:
            category.clean()

        self.assertEqual(set(raised.exception.message_dict), {'account'})

    def test_income_category_rejects_expense_account(self):
        category = IncomeCategory(
            owner_id=1,
            name='Sales',
            account=self.build_account(account_type=Account.AccountType.EXPENSE),
        )

        with self.assertRaises(ValidationError) as raised:
            category.clean()

        self.assertEqual(
            raised.exception.message_dict['account'],
            ['Income category must use an income account.'],
        )
