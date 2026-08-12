from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ponds.models import Pond
from stocks.models import FishStock


class Account(models.Model):
    class AccountType(models.TextChoices):
        ASSET = 'asset', 'Asset'
        EXPENSE = 'expense', 'Expense'
        INCOME = 'income', 'Income'
        LIABILITY = 'liability', 'Liability'
        EQUITY = 'equity', 'Equity'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_accounts',
    )
    name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=16, choices=AccountType.choices)
    code = models.CharField(max_length=24, blank=True)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['account_type', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_financial_account_name_per_owner',
            ),
        ]

    def clean(self):
        if not (self.name or '').strip():
            raise ValidationError({'name': 'Account name is required.'})

    def __str__(self):
        return f'{self.name} ({self.get_account_type_display()})'


class ExpenseCategory(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expense_categories',
    )
    name = models.CharField(max_length=120)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name='expense_categories',
        null=True,
        blank=True,
    )
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_expense_category_name_per_owner',
            ),
        ]

    def clean(self):
        if not (self.name or '').strip():
            raise ValidationError({'name': 'Category name is required.'})
        if self.account and self.account.owner_id != self.owner_id:
            raise ValidationError({'account': 'Category account must belong to the same owner.'})
        if self.account and self.account.account_type != Account.AccountType.EXPENSE:
            raise ValidationError({'account': 'Expense category must use an expense account.'})

    def __str__(self):
        return self.name


class IncomeCategory(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='income_categories',
    )
    name = models.CharField(max_length=120)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        related_name='income_categories',
        null=True,
        blank=True,
    )
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_income_category_name_per_owner',
            ),
        ]

    def clean(self):
        if not (self.name or '').strip():
            raise ValidationError({'name': 'Category name is required.'})
        if self.account and self.account.owner_id != self.owner_id:
            raise ValidationError({'account': 'Category account must belong to the same owner.'})
        if self.account and self.account.account_type != Account.AccountType.INCOME:
            raise ValidationError({'account': 'Income category must use an income account.'})

    def __str__(self):
        return self.name


class FinancialTransaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    class SourceType(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        FEED_PURCHASE = 'feed_purchase', 'Feed purchase'
        MEAL_FEED = 'meal_feed', 'Meal feed'
        FISH_STOCKING = 'fish_stocking', 'Fish stocking'
        MEDICINE_TREATMENT = 'medicine_treatment', 'Medicine or treatment'
        LABOR = 'labor', 'Labor'
        HARVEST_SALE = 'harvest_sale', 'Harvest sale'
        POND_MAINTENANCE = 'pond_maintenance', 'Pond maintenance'
        EQUIPMENT_PURCHASE = 'equipment_purchase', 'Equipment purchase'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_transactions',
    )
    pond = models.ForeignKey(
        Pond,
        on_delete=models.SET_NULL,
        related_name='financial_transactions',
        null=True,
        blank=True,
    )
    fish_stock = models.ForeignKey(
        FishStock,
        on_delete=models.SET_NULL,
        related_name='financial_transactions',
        null=True,
        blank=True,
    )
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        related_name='transactions',
        null=True,
        blank=True,
    )
    income_category = models.ForeignKey(
        IncomeCategory,
        on_delete=models.SET_NULL,
        related_name='transactions',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=32, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transaction_date = models.DateField()
    source_type = models.CharField(
        max_length=32,
        choices=SourceType.choices,
        default=SourceType.MANUAL,
    )
    source_id = models.PositiveIntegerField(null=True, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    is_automatic = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['owner', '-transaction_date']),
            models.Index(fields=['pond', '-transaction_date']),
            models.Index(fields=['transaction_type', 'source_type']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='financial_transaction_amount_positive',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(quantity__isnull=True)
                    | models.Q(quantity__gt=0)
                ),
                name='financial_transaction_quantity_positive_when_set',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(unit_price__isnull=True)
                    | models.Q(unit_price__gte=0)
                ),
                name='financial_transaction_unit_price_not_negative_when_set',
            ),
        ]

    def clean(self):
        errors = {}

        if not (self.title or '').strip():
            errors['title'] = 'Transaction title is required.'
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = 'Amount must be greater than zero.'
        if self.pond and self.pond.owner_id != self.owner_id:
            errors['pond'] = 'Pond must belong to the transaction owner.'
        if self.fish_stock and self.pond and self.fish_stock.pond_id != self.pond_id:
            errors['fish_stock'] = 'Fish stock must belong to the selected pond.'
        if self.expense_category and self.expense_category.owner_id != self.owner_id:
            errors['expense_category'] = 'Expense category must belong to the transaction owner.'
        if self.income_category and self.income_category.owner_id != self.owner_id:
            errors['income_category'] = 'Income category must belong to the transaction owner.'
        if self.transaction_type == self.TransactionType.EXPENSE and not self.expense_category_id:
            errors['expense_category'] = 'Expense category is required for expense transactions.'
        if self.transaction_type == self.TransactionType.INCOME and not self.income_category_id:
            errors['income_category'] = 'Income category is required for income transactions.'
        if self.transaction_type == self.TransactionType.EXPENSE and self.income_category_id:
            errors['income_category'] = 'Income category cannot be used on expense transactions.'
        if self.transaction_type == self.TransactionType.INCOME and self.expense_category_id:
            errors['expense_category'] = 'Expense category cannot be used on income transactions.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.get_transaction_type_display()}: {self.title}'


class TransactionLine(models.Model):
    class EntryType(models.TextChoices):
        DEBIT = 'debit', 'Debit'
        CREDIT = 'credit', 'Credit'

    transaction = models.ForeignKey(
        FinancialTransaction,
        on_delete=models.CASCADE,
        related_name='lines',
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transaction_lines',
    )
    entry_type = models.CharField(max_length=8, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    memo = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='transaction_line_amount_positive',
            ),
        ]

    def clean(self):
        if self.account.owner_id != self.transaction.owner_id:
            raise ValidationError({'account': 'Line account must belong to the transaction owner.'})
        if self.amount is not None and self.amount <= Decimal('0'):
            raise ValidationError({'amount': 'Line amount must be greater than zero.'})

    def __str__(self):
        return f'{self.get_entry_type_display()} {self.account}: {self.amount}'


class Budget(models.Model):
    class PeriodType(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        POND_CYCLE = 'pond_cycle', 'Pond cycle'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_budgets',
    )
    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='financial_budgets',
        null=True,
        blank=True,
    )
    expense_category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        related_name='budgets',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=140)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period_type = models.CharField(
        max_length=16,
        choices=PeriodType.choices,
        default=PeriodType.MONTHLY,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', 'name']
        indexes = [
            models.Index(fields=['owner', 'period_type', 'start_date']),
            models.Index(fields=['pond', 'start_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='financial_budget_amount_positive',
            ),
        ]

    def clean(self):
        errors = {}

        if not (self.name or '').strip():
            errors['name'] = 'Budget name is required.'
        if self.amount is not None and self.amount <= 0:
            errors['amount'] = 'Budget amount must be greater than zero.'
        if self.pond and self.pond.owner_id != self.owner_id:
            errors['pond'] = 'Budget pond must belong to the owner.'
        if self.expense_category and self.expense_category.owner_id != self.owner_id:
            errors['expense_category'] = 'Budget category must belong to the owner.'
        if self.end_date and self.end_date < self.start_date:
            errors['end_date'] = 'End date cannot be before start date.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name
