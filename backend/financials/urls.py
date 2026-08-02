from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    AnalyticsView,
    AutomaticFinancialRecordView,
    BudgetViewSet,
    ExpenseCategoryViewSet,
    FeedCostAnalysisView,
    FinancialDashboardView,
    FinancialTransactionViewSet,
    HarvestRevenueEstimatorView,
    IncomeCategoryViewSet,
    PondPerformanceView,
    ProfitLossView,
)


router = DefaultRouter()
router.register('accounts', AccountViewSet, basename='financial-account')
router.register('expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register('income-categories', IncomeCategoryViewSet, basename='income-category')
router.register('transactions', FinancialTransactionViewSet, basename='financial-transaction')
router.register('budgets', BudgetViewSet, basename='financial-budget')

urlpatterns = [
    path('dashboard/', FinancialDashboardView.as_view(), name='financial-dashboard'),
    path('profit-loss/', ProfitLossView.as_view(), name='financial-profit-loss'),
    path('pond-performance/', PondPerformanceView.as_view(), name='financial-pond-performance'),
    path('feed-cost-analysis/', FeedCostAnalysisView.as_view(), name='financial-feed-cost-analysis'),
    path('harvest-revenue-estimator/', HarvestRevenueEstimatorView.as_view(), name='harvest-revenue-estimator'),
    path('analytics/', AnalyticsView.as_view(), name='financial-analytics'),
    path('automatic-records/', AutomaticFinancialRecordView.as_view(), name='automatic-financial-records'),
    path('', include(router.urls)),
]
