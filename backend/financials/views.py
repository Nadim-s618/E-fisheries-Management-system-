from decimal import Decimal, InvalidOperation

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ponds.models import Pond

from .models import (
    Account,
    Budget,
    ExpenseCategory,
    FinancialTransaction,
    IncomeCategory,
)
from .serializers import (
    AccountSerializer,
    BudgetSerializer,
    ExpenseCategorySerializer,
    FinancialTransactionSerializer,
    IncomeCategorySerializer,
)
from .services import (
    active_budgets_with_actuals,
    budget_actual_spend,
    create_automatic_financial_record,
    ensure_default_financial_setup,
    month_bounds,
    sum_transactions,
)


def user_ponds(user):
    if user.is_staff:
        return Pond.objects.select_related('owner').all()
    return Pond.objects.select_related('owner').filter(owner=user)


def user_transactions(user):
    queryset = FinancialTransaction.objects.select_related(
        'owner',
        'pond',
        'fish_stock',
        'expense_category',
        'income_category',
    ).prefetch_related('lines', 'lines__account')

    if user.is_staff:
        return queryset.all()

    return queryset.filter(owner=user)


def apply_transaction_filters(queryset, request):
    pond_id = request.query_params.get('pond')
    transaction_type = request.query_params.get('type') or request.query_params.get('transaction_type')
    source_type = request.query_params.get('source_type')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    if pond_id:
        if not pond_id.isdigit():
            raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
        queryset = queryset.filter(pond_id=pond_id)
    if transaction_type:
        valid_types = {choice[0] for choice in FinancialTransaction.TransactionType.choices}
        if transaction_type not in valid_types:
            raise ValidationError({'type': f'Type must be one of: {", ".join(sorted(valid_types))}.'})
        queryset = queryset.filter(transaction_type=transaction_type)
    if source_type:
        valid_sources = {choice[0] for choice in FinancialTransaction.SourceType.choices}
        if source_type not in valid_sources:
            raise ValidationError({'source_type': f'Source type must be one of: {", ".join(sorted(valid_sources))}.'})
        queryset = queryset.filter(source_type=source_type)
    if start_date:
        parsed = parse_date(start_date)
        if parsed is None:
            raise ValidationError({'start_date': 'Date must use YYYY-MM-DD format.'})
        queryset = queryset.filter(transaction_date__gte=parsed)
    if end_date:
        parsed = parse_date(end_date)
        if parsed is None:
            raise ValidationError({'end_date': 'Date must use YYYY-MM-DD format.'})
        queryset = queryset.filter(transaction_date__lte=parsed)

    return queryset


def money(value):
    return value or Decimal('0')


def percent(numerator, denominator):
    denominator = Decimal(str(denominator or 0))
    if denominator == 0:
        return 0
    return round(float((Decimal(str(numerator or 0)) / denominator) * 100), 2)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        ensure_default_financial_setup(self.request.user)
        queryset = Account.objects.filter(owner=self.request.user)
        account_type = self.request.query_params.get('type')
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseCategorySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        ensure_default_financial_setup(self.request.user)
        return ExpenseCategory.objects.select_related('account').filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class IncomeCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = IncomeCategorySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        ensure_default_financial_setup(self.request.user)
        return IncomeCategory.objects.select_related('account').filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FinancialTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        ensure_default_financial_setup(self.request.user)
        return apply_transaction_filters(user_transactions(self.request.user), self.request)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        ensure_default_financial_setup(self.request.user)
        queryset = Budget.objects.select_related('pond', 'expense_category').filter(owner=self.request.user)
        pond_id = self.request.query_params.get('pond')
        active = self.request.query_params.get('active')

        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            queryset = queryset.filter(pond_id=pond_id)
        if active in {'true', '1', 'yes'}:
            queryset = queryset.filter(is_active=True)
        if active in {'false', '0', 'no'}:
            queryset = queryset.filter(is_active=False)

        return queryset

    def list(self, request, *args, **kwargs):
        budgets = list(self.get_queryset())
        self.add_budget_actuals(budgets)
        serializer = self.get_serializer(budgets, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        budget = self.get_object()
        self.add_budget_actuals([budget])
        serializer = self.get_serializer(budget)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def add_budget_actuals(self, budgets):
        for budget in budgets:
            actual = budget_actual_spend(self.request.user, budget)
            budget.actual_spend = actual
            budget.remaining = budget.amount - actual
            budget.used_percent = percent(actual, budget.amount)


class FinancialDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ensure_default_financial_setup(request.user)
        start, end = self.get_bounds(request)
        transactions = user_transactions(request.user).filter(
            transaction_date__gte=start,
            transaction_date__lte=end,
        )
        pond = self.get_pond(request)
        if pond is not None:
            transactions = transactions.filter(pond=pond)

        income = sum_transactions(transactions, FinancialTransaction.TransactionType.INCOME)
        expenses = sum_transactions(transactions, FinancialTransaction.TransactionType.EXPENSE)
        profit = income - expenses
        budgets = [
            row
            for row in active_budgets_with_actuals(request.user)
            if pond is None or row['budget'].pond_id in {None, pond.id}
        ]
        over_budget_count = sum(1 for row in budgets if row['actual'] > row['budget'].amount)
        budget_alerts = [
            row
            for row in budgets
            if percent(row['actual'], row['budget'].amount) >= 80
        ]

        return Response({
            'period': {
                'start_date': start,
                'end_date': end,
            },
            'summary': {
                'income': income,
                'expenses': expenses,
                'profit': profit,
                'profit_margin_percent': percent(profit, income),
                'transaction_count': transactions.count(),
                'automatic_record_count': transactions.filter(is_automatic=True).count(),
                'active_budget_count': len(budgets),
                'over_budget_count': over_budget_count,
            },
            'recent_transactions': FinancialTransactionSerializer(
                transactions[:8],
                many=True,
                context={'request': request},
            ).data,
            'expense_breakdown': self.category_breakdown(
                transactions,
                FinancialTransaction.TransactionType.EXPENSE,
                'expense_category__name',
            ),
            'income_breakdown': self.category_breakdown(
                transactions,
                FinancialTransaction.TransactionType.INCOME,
                'income_category__name',
            ),
            'monthly_trend': monthly_trend(transactions),
            'budget_alerts': [
                {
                    'id': row['budget'].id,
                    'name': row['budget'].name,
                    'pond_name': row['budget'].pond.name if row['budget'].pond else 'All ponds',
                    'amount': row['budget'].amount,
                    'actual_spend': row['actual'],
                    'remaining': row['budget'].amount - row['actual'],
                    'used_percent': percent(row['actual'], row['budget'].amount),
                }
                for row in budget_alerts
            ],
        })

    def get_pond(self, request):
        pond_id = request.query_params.get('pond')
        if not pond_id:
            return None
        if not pond_id.isdigit():
            raise ValidationError({'pond': 'Pond must be a valid numeric id.'})

        pond = user_ponds(request.user).filter(pk=pond_id).first()
        if pond is None:
            raise ValidationError({'pond': 'Pond not found.'})

        return pond

    def get_bounds(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date and not end_date:
            return month_bounds()

        start = parse_date(start_date) if start_date else timezone.now().date().replace(day=1)
        end = parse_date(end_date) if end_date else timezone.now().date()

        if start is None:
            raise ValidationError({'start_date': 'Date must use YYYY-MM-DD format.'})
        if end is None:
            raise ValidationError({'end_date': 'Date must use YYYY-MM-DD format.'})
        if end < start:
            raise ValidationError({'end_date': 'End date cannot be before start date.'})

        return start, end

    def category_breakdown(self, queryset, transaction_type, category_field):
        rows = (
            queryset
            .filter(transaction_type=transaction_type)
            .values(category_field)
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )
        return [
            {
                'category': row[category_field] or 'Uncategorized',
                'total': money(row['total']),
                'count': row['count'],
            }
            for row in rows
        ]


class ProfitLossView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ensure_default_financial_setup(request.user)
        transactions = apply_transaction_filters(user_transactions(request.user), request)
        income = sum_transactions(transactions, FinancialTransaction.TransactionType.INCOME)
        expenses = sum_transactions(transactions, FinancialTransaction.TransactionType.EXPENSE)
        income_transactions = transactions.filter(transaction_type=FinancialTransaction.TransactionType.INCOME)
        expense_transactions = transactions.filter(transaction_type=FinancialTransaction.TransactionType.EXPENSE)
        automatic_income = sum_transactions(
            income_transactions.filter(is_automatic=True),
            FinancialTransaction.TransactionType.INCOME,
        )
        automatic_expenses = sum_transactions(
            expense_transactions.filter(is_automatic=True),
            FinancialTransaction.TransactionType.EXPENSE,
        )

        return Response({
            'income': income,
            'expenses': expenses,
            'income_manual': income - automatic_income,
            'income_automatic': automatic_income,
            'expenses_manual': expenses - automatic_expenses,
            'expenses_automatic': automatic_expenses,
            'gross_profit': income - expenses,
            'net_profit': income - expenses,
            'profit_margin_percent': percent(income - expenses, income),
            'expense_breakdown': breakdown(transactions, 'expense', 'expense_category__name'),
            'income_breakdown': breakdown(transactions, 'income', 'income_category__name'),
            'monthly_trend': monthly_trend(transactions),
        })


class PondPerformanceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ensure_default_financial_setup(request.user)
        ponds = user_ponds(request.user)
        transactions = apply_transaction_filters(user_transactions(request.user), request)
        pond_id = request.query_params.get('pond')
        if pond_id:
            ponds = ponds.filter(pk=pond_id)
        results = []

        for pond in ponds:
            pond_transactions = transactions.filter(pond=pond)
            income = sum_transactions(pond_transactions, FinancialTransaction.TransactionType.INCOME)
            expenses = sum_transactions(pond_transactions, FinancialTransaction.TransactionType.EXPENSE)
            results.append({
                'pond_id': pond.id,
                'pond_name': pond.name,
                'income': income,
                'expenses': expenses,
                'profit': income - expenses,
                'profit_margin_percent': percent(income - expenses, income),
                'transaction_count': pond_transactions.count(),
            })

        return Response({
            'ponds': sorted(results, key=lambda row: row['profit'], reverse=True),
        })


class AnalyticsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ensure_default_financial_setup(request.user)
        transactions = apply_transaction_filters(user_transactions(request.user), request)

        return Response({
            'monthly_trend': monthly_trend(transactions),
            'source_breakdown': source_breakdown(transactions),
            'top_expenses': breakdown(transactions, 'expense', 'expense_category__name')[:6],
            'top_income': breakdown(transactions, 'income', 'income_category__name')[:6],
            'pond_performance': PondPerformanceView().get(request).data['ponds'][:6],
        })


class AutomaticFinancialRecordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            financial_transaction = create_automatic_financial_record(request.user, request.data)
        except ValueError as exc:
            return Response({'source_type': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (InvalidOperation, TypeError):
            return Response({'amount': 'Amount must be a valid number.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FinancialTransactionSerializer(
            financial_transaction,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def breakdown(queryset, transaction_type, field):
    rows = (
        queryset
        .filter(transaction_type=transaction_type)
        .values(field)
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )
    return [
        {
            'name': row[field] or 'Uncategorized',
            'total': money(row['total']),
            'count': row['count'],
        }
        for row in rows
    ]


def source_breakdown(queryset):
    rows = (
        queryset
        .values('source_type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )
    labels = dict(FinancialTransaction.SourceType.choices)
    return [
        {
            'source_type': row['source_type'],
            'label': labels.get(row['source_type'], row['source_type']),
            'total': money(row['total']),
            'count': row['count'],
        }
        for row in rows
    ]


def monthly_trend(queryset):
    rows = (
        queryset
        .annotate(month=TruncMonth('transaction_date'))
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    by_month = {}

    for row in rows:
        month_key = row['month'].isoformat()
        by_month.setdefault(month_key, {
            'month': month_key,
            'income': Decimal('0'),
            'expenses': Decimal('0'),
            'profit': Decimal('0'),
        })
        if row['transaction_type'] == FinancialTransaction.TransactionType.INCOME:
            by_month[month_key]['income'] = money(row['total'])
        else:
            by_month[month_key]['expenses'] = money(row['total'])

    for row in by_month.values():
        row['profit'] = row['income'] - row['expenses']

    return list(by_month.values())
