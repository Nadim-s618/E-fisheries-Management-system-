from django.contrib import admin

from .models import (
    Account,
    Budget,
    ExpenseCategory,
    FinancialTransaction,
    IncomeCategory,
    TransactionLine,
)


class TransactionLineInline(admin.TabularInline):
    model = TransactionLine
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'account_type', 'code', 'is_active')
    list_filter = ('account_type', 'is_active', 'is_system')
    search_fields = ('name', 'owner__username', 'code')


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'account', 'is_active')
    list_filter = ('is_active', 'is_system')
    search_fields = ('name', 'owner__username')


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'account', 'is_active')
    list_filter = ('is_active', 'is_system')
    search_fields = ('name', 'owner__username')


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'pond',
        'transaction_type',
        'amount',
        'transaction_date',
        'source_type',
        'is_automatic',
    )
    list_filter = ('transaction_type', 'source_type', 'is_automatic', 'transaction_date')
    search_fields = ('title', 'description', 'reference', 'pond__name', 'owner__username')
    inlines = (TransactionLineInline,)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'pond', 'expense_category', 'amount', 'period_type', 'start_date', 'is_active')
    list_filter = ('period_type', 'is_active', 'start_date')
    search_fields = ('name', 'pond__name', 'owner__username')
