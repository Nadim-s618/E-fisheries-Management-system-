from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

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
from .services import ensure_default_financial_setup, sync_transaction_lines


class AccountSerializer(serializers.ModelSerializer):
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)

    class Meta:
        model = Account
        fields = (
            'id',
            'name',
            'account_type',
            'account_type_display',
            'code',
            'is_system',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'is_system', 'created_at', 'updated_at')


class ExpenseCategorySerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = ExpenseCategory
        fields = (
            'id',
            'name',
            'account',
            'account_name',
            'is_system',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'account_name', 'is_system', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['account'].queryset = Account.objects.filter(
                owner=request.user,
                account_type=Account.AccountType.EXPENSE,
            )


class IncomeCategorySerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = IncomeCategory
        fields = (
            'id',
            'name',
            'account',
            'account_name',
            'is_system',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'account_name', 'is_system', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['account'].queryset = Account.objects.filter(
                owner=request.user,
                account_type=Account.AccountType.INCOME,
            )


class TransactionLineSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = TransactionLine
        fields = ('id', 'account', 'account_name', 'entry_type', 'amount', 'memo')
        read_only_fields = fields


class FinancialTransactionSerializer(serializers.ModelSerializer):
    extra_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
        write_only=True,
    )
    pond_name = serializers.CharField(source='pond.name', read_only=True)
    fish_stock_name = serializers.CharField(source='fish_stock.batch_name', read_only=True)
    expense_category_name = serializers.CharField(source='expense_category.name', read_only=True)
    income_category_name = serializers.CharField(source='income_category.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    lines = TransactionLineSerializer(many=True, read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            'id',
            'pond',
            'pond_name',
            'fish_stock',
            'fish_stock_name',
            'transaction_type',
            'transaction_type_display',
            'expense_category',
            'expense_category_name',
            'income_category',
            'income_category_name',
            'title',
            'description',
            'amount',
            'quantity',
            'unit',
            'unit_price',
            'extra_amount',
            'transaction_date',
            'source_type',
            'source_type_display',
            'source_id',
            'reference',
            'is_automatic',
            'lines',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'pond_name',
            'fish_stock_name',
            'expense_category_name',
            'income_category_name',
            'transaction_type_display',
            'source_type_display',
            'is_automatic',
            'lines',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'amount': {'required': False},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            ensure_default_financial_setup(request.user)
            self.fields['pond'].queryset = Pond.objects.filter(owner=request.user)
            self.fields['fish_stock'].queryset = FishStock.objects.filter(pond__owner=request.user)
            self.fields['expense_category'].queryset = ExpenseCategory.objects.filter(owner=request.user)
            self.fields['income_category'].queryset = IncomeCategory.objects.filter(owner=request.user)

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        owner = getattr(request, 'user', None)
        instance = self.instance
        transaction_type = attrs.get('transaction_type', getattr(instance, 'transaction_type', None))
        pond = attrs.get('pond', getattr(instance, 'pond', None))
        fish_stock = attrs.get('fish_stock', getattr(instance, 'fish_stock', None))
        expense_category = attrs.get('expense_category', getattr(instance, 'expense_category', None))
        income_category = attrs.get('income_category', getattr(instance, 'income_category', None))
        quantity = attrs.get('quantity', getattr(instance, 'quantity', None))
        unit_price = attrs.get('unit_price', getattr(instance, 'unit_price', None))
        extra_amount = attrs.pop('extra_amount', None) or Decimal('0')

        if quantity is not None and unit_price is not None:
            attrs['amount'] = (quantity * unit_price + extra_amount).quantize(Decimal('0.01'))

        if not attrs.get('amount') or attrs['amount'] <= Decimal('0'):
            raise serializers.ValidationError({'amount': 'Amount must be greater than zero.'})

        if pond and owner and not owner.is_staff and pond.owner_id != owner.id:
            raise serializers.ValidationError({'pond': 'Pond not found.'})
        if fish_stock and pond and fish_stock.pond_id != pond.id:
            raise serializers.ValidationError({'fish_stock': 'Fish stock must belong to the selected pond.'})
        if transaction_type == FinancialTransaction.TransactionType.EXPENSE:
            if not expense_category:
                raise serializers.ValidationError({'expense_category': 'Expense category is required.'})
            attrs['income_category'] = None
        if transaction_type == FinancialTransaction.TransactionType.INCOME:
            if not income_category:
                raise serializers.ValidationError({'income_category': 'Income category is required.'})
            attrs['expense_category'] = None

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context['request']
        financial_transaction = FinancialTransaction.objects.create(
            owner=request.user,
            **validated_data,
        )
        sync_transaction_lines(financial_transaction)
        return financial_transaction

    @transaction.atomic
    def update(self, instance, validated_data):
        financial_transaction = super().update(instance, validated_data)
        sync_transaction_lines(financial_transaction)
        return financial_transaction


class BudgetSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)
    expense_category_name = serializers.CharField(source='expense_category.name', read_only=True)
    actual_spend = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    used_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = Budget
        fields = (
            'id',
            'pond',
            'pond_name',
            'expense_category',
            'expense_category_name',
            'name',
            'amount',
            'period_type',
            'start_date',
            'end_date',
            'notes',
            'is_active',
            'actual_spend',
            'remaining',
            'used_percent',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'pond_name',
            'expense_category_name',
            'actual_spend',
            'remaining',
            'used_percent',
            'created_at',
            'updated_at',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            ensure_default_financial_setup(request.user)
            self.fields['pond'].queryset = Pond.objects.filter(owner=request.user)
            self.fields['expense_category'].queryset = ExpenseCategory.objects.filter(owner=request.user)

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Budget amount must be greater than zero.')
        return value

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date cannot be before start date.'})

        return attrs
