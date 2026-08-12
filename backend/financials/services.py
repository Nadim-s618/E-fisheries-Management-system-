from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from ponds.models import Pond
from stocks.models import FishStock

from .models import (
    Account,
    Budget,
    ExpenseCategory,
    FinancialTransaction,
    IncomeCategory,
    TransactionLine,
)


DEFAULT_ACCOUNTS = [
    ('Cash', Account.AccountType.ASSET, '1000'),
    ('Feed Expense', Account.AccountType.EXPENSE, '5000'),
    ('Fish Stocking Expense', Account.AccountType.EXPENSE, '5100'),
    ('Medicine & Treatment Expense', Account.AccountType.EXPENSE, '5200'),
    ('Labor Expense', Account.AccountType.EXPENSE, '5300'),
    ('Pond Maintenance Expense', Account.AccountType.EXPENSE, '5400'),
    ('Equipment Expense', Account.AccountType.EXPENSE, '5500'),
    ('Other Expense', Account.AccountType.EXPENSE, '5999'),
    ('Harvest Sales', Account.AccountType.INCOME, '4000'),
    ('Other Income', Account.AccountType.INCOME, '4999'),
]

DEFAULT_EXPENSE_CATEGORIES = [
    ('Feed', 'Feed Expense'),
    ('Fish Stocking', 'Fish Stocking Expense'),
    ('Medicine & Treatment', 'Medicine & Treatment Expense'),
    ('Labor', 'Labor Expense'),
    ('Pond Maintenance', 'Pond Maintenance Expense'),
    ('Equipment', 'Equipment Expense'),
    ('Other Expense', 'Other Expense'),
]

DEFAULT_INCOME_CATEGORIES = [
    ('Harvest Sales', 'Harvest Sales'),
    ('Other Income', 'Other Income'),
]

SOURCE_DEFAULTS = {
    FinancialTransaction.SourceType.FEED_PURCHASE: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Feed',
        'title': 'Feed purchase',
        'unit': 'kg',
    },
    FinancialTransaction.SourceType.MEAL_FEED: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Feed',
        'title': 'Meal feed cost',
        'unit': 'kg',
    },
    FinancialTransaction.SourceType.FISH_STOCKING: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Fish Stocking',
        'title': 'Fish stocking',
        'unit': 'fish',
    },
    FinancialTransaction.SourceType.MEDICINE_TREATMENT: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Medicine & Treatment',
        'title': 'Medicine or treatment',
    },
    FinancialTransaction.SourceType.LABOR: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Labor',
        'title': 'Labor cost',
    },
    FinancialTransaction.SourceType.HARVEST_SALE: {
        'transaction_type': FinancialTransaction.TransactionType.INCOME,
        'income_category': 'Harvest Sales',
        'title': 'Harvest sale',
        'unit': 'kg',
    },
    FinancialTransaction.SourceType.POND_MAINTENANCE: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Pond Maintenance',
        'title': 'Pond maintenance',
    },
    FinancialTransaction.SourceType.EQUIPMENT_PURCHASE: {
        'transaction_type': FinancialTransaction.TransactionType.EXPENSE,
        'expense_category': 'Equipment',
        'title': 'Equipment purchase',
    },
}


def ensure_default_financial_setup(user):
    accounts_by_name = {}

    for name, account_type, code in DEFAULT_ACCOUNTS:
        account, _ = Account.objects.get_or_create(
            owner=user,
            name=name,
            defaults={
                'account_type': account_type,
                'code': code,
                'is_system': True,
            },
        )
        accounts_by_name[name] = account

    for name, account_name in DEFAULT_EXPENSE_CATEGORIES:
        ExpenseCategory.objects.get_or_create(
            owner=user,
            name=name,
            defaults={
                'account': accounts_by_name.get(account_name),
                'is_system': True,
            },
        )

    for name, account_name in DEFAULT_INCOME_CATEGORIES:
        IncomeCategory.objects.get_or_create(
            owner=user,
            name=name,
            defaults={
                'account': accounts_by_name.get(account_name),
                'is_system': True,
            },
        )


def get_cash_account(user):
    ensure_default_financial_setup(user)
    return Account.objects.get(owner=user, name='Cash')


def get_expense_category(user, name):
    ensure_default_financial_setup(user)
    return ExpenseCategory.objects.select_related('account').get(owner=user, name=name)


def get_income_category(user, name):
    ensure_default_financial_setup(user)
    return IncomeCategory.objects.select_related('account').get(owner=user, name=name)


@transaction.atomic
def sync_transaction_lines(financial_transaction):
    financial_transaction.lines.all().delete()
    cash_account = get_cash_account(financial_transaction.owner)

    if financial_transaction.transaction_type == FinancialTransaction.TransactionType.EXPENSE:
        category_account = financial_transaction.expense_category.account
        debit_account = category_account or Account.objects.get(
            owner=financial_transaction.owner,
            name='Other Expense',
        )
        lines = [
            TransactionLine(
                transaction=financial_transaction,
                account=debit_account,
                entry_type=TransactionLine.EntryType.DEBIT,
                amount=financial_transaction.amount,
                memo=financial_transaction.title,
            ),
            TransactionLine(
                transaction=financial_transaction,
                account=cash_account,
                entry_type=TransactionLine.EntryType.CREDIT,
                amount=financial_transaction.amount,
                memo=financial_transaction.title,
            ),
        ]
    else:
        category_account = financial_transaction.income_category.account
        credit_account = category_account or Account.objects.get(
            owner=financial_transaction.owner,
            name='Other Income',
        )
        lines = [
            TransactionLine(
                transaction=financial_transaction,
                account=cash_account,
                entry_type=TransactionLine.EntryType.DEBIT,
                amount=financial_transaction.amount,
                memo=financial_transaction.title,
            ),
            TransactionLine(
                transaction=financial_transaction,
                account=credit_account,
                entry_type=TransactionLine.EntryType.CREDIT,
                amount=financial_transaction.amount,
                memo=financial_transaction.title,
            ),
        ]

    TransactionLine.objects.bulk_create(lines)


@transaction.atomic
def create_automatic_financial_record(user, payload):
    ensure_default_financial_setup(user)
    source_type = payload.get('source_type')
    defaults = SOURCE_DEFAULTS.get(source_type)

    if defaults is None:
        raise ValueError('Unsupported automatic source type.')

    source_id = payload.get('source_id') or None
    if source_id:
        existing = FinancialTransaction.objects.filter(
            owner=user,
            source_type=source_type,
            source_id=source_id,
        ).first()
        if existing:
            return existing

    pond_id = payload.get('pond')
    fish_stock_id = payload.get('fish_stock') or None
    pond = None
    fish_stock = None

    if pond_id:
        pond_queryset = Pond.objects.all() if user.is_staff else Pond.objects.filter(owner=user)
        pond = pond_queryset.filter(pk=pond_id).first()
        if pond is None:
            raise ValueError('Pond not found.')

    if fish_stock_id:
        stock_queryset = FishStock.objects.select_related('pond')
        if not user.is_staff:
            stock_queryset = stock_queryset.filter(pond__owner=user)
        fish_stock = stock_queryset.filter(pk=fish_stock_id).first()
        if fish_stock is None:
            raise ValueError('Fish stock not found.')
        if pond and fish_stock.pond_id != pond.id:
            raise ValueError('Fish stock must belong to the selected pond.')

    transaction_type = defaults['transaction_type']
    quantity = payload.get('quantity') or None
    unit_price = payload.get('unit_price') or None
    extra_amount = Decimal(str(payload.get('extra_amount') or '0'))
    amount = Decimal(str(payload.get('amount') or '0'))
    if quantity is not None and unit_price is not None:
        amount = (Decimal(str(quantity)) * Decimal(str(unit_price)) + extra_amount).quantize(Decimal('0.01'))

    transaction_data = {
        'owner': user,
        'pond': pond,
        'fish_stock': fish_stock,
        'transaction_type': transaction_type,
        'title': payload.get('title') or defaults['title'],
        'description': payload.get('description', ''),
        'amount': amount,
        'quantity': quantity,
        'unit': payload.get('unit') or defaults.get('unit', ''),
        'unit_price': unit_price,
        'transaction_date': payload.get('transaction_date') or date.today(),
        'source_type': source_type,
        'source_id': source_id,
        'reference': payload.get('reference', ''),
        'is_automatic': True,
    }

    if transaction_type == FinancialTransaction.TransactionType.EXPENSE:
        transaction_data['expense_category'] = get_expense_category(user, defaults['expense_category'])
    else:
        transaction_data['income_category'] = get_income_category(user, defaults['income_category'])

    financial_transaction = FinancialTransaction.objects.create(**transaction_data)
    sync_transaction_lines(financial_transaction)
    return financial_transaction


def month_bounds(value=None):
    today = value or date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    return start, end


def sum_transactions(queryset, transaction_type):
    value = queryset.filter(transaction_type=transaction_type).aggregate(total=Sum('amount'))['total']
    return value or Decimal('0')


def budget_spend_queryset(user, budget):
    queryset = FinancialTransaction.objects.filter(
        owner=user,
        transaction_type=FinancialTransaction.TransactionType.EXPENSE,
        transaction_date__gte=budget.start_date,
    )

    if budget.end_date:
        queryset = queryset.filter(transaction_date__lte=budget.end_date)
    if budget.pond_id:
        queryset = queryset.filter(pond=budget.pond)
    if budget.expense_category_id:
        queryset = queryset.filter(expense_category=budget.expense_category)

    return queryset


def budget_actual_spend(user, budget):
    return budget_spend_queryset(user, budget).aggregate(total=Sum('amount'))['total'] or Decimal('0')


def active_budgets_with_actuals(user):
    budgets = Budget.objects.select_related('pond', 'expense_category').filter(owner=user, is_active=True)
    return [
        {
            'budget': budget,
            'actual': budget_actual_spend(user, budget),
        }
        for budget in budgets
    ]
