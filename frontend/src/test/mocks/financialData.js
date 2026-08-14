export const financialPonds = [
  { id: 1, name: 'North Pond' },
  { id: 2, name: 'South Pond' },
];

export const expenseCategories = [
  { id: 11, name: 'Feed' },
  { id: 12, name: 'Labor' },
];

export const incomeCategories = [
  { id: 21, name: 'Fish Sales' },
];

export const financialDashboard = {
  summary: {
    income: 250000,
    expenses: 100000,
    profit: 150000,
    automatic_record_count: 8,
    active_budget_count: 2,
    over_budget_count: 1,
  },
  budget_alerts: [],
  monthly_trend: [{ month: '2026-08', income: 250000, expenses: 100000 }],
  expense_breakdown: [{ category: 'Feed', total: 70000 }],
  recent_transactions: [
    {
      id: 301,
      transaction_date: '2026-08-14',
      title: 'Feed purchase',
      pond_name: 'North Pond',
      expense_category_name: 'Feed',
      is_automatic: false,
      transaction_type: 'expense',
      amount: 12500,
      reference: 'INV-001',
    },
  ],
};

export const financialTransactions = [
  ...financialDashboard.recent_transactions,
  {
    id: 302,
    transaction_date: '2026-08-12',
    title: 'Harvest sale',
    pond_name: 'South Pond',
    income_category_name: 'Fish Sales',
    is_automatic: true,
    source_type_display: 'Harvest Sale',
    source_type: 'harvest_sale',
    transaction_type: 'income',
    amount: 250000,
    reference: 'SALE-001',
  },
];

export const financialBudgets = [
  {
    id: 401,
    name: 'Monthly Feed Budget',
    amount: 80000,
    actual_spend: 70000,
    remaining: 10000,
    used_percent: 87.5,
    period_type: 'monthly',
    pond_name: 'North Pond',
    expense_category_name: 'Feed',
  },
];

export const profitLoss = {
  income: 250000,
  expenses: 100000,
  net_profit: 150000,
  profit_margin_percent: 60,
  income_manual: 0,
  income_automatic: 250000,
  expenses_manual: 30000,
  expenses_automatic: 70000,
  income_breakdown: [{ name: 'Fish Sales', total: 250000 }],
  expense_breakdown: [{ name: 'Feed', total: 70000 }],
};

export const pondPerformance = {
  ponds: [
    { pond_id: 1, pond_name: 'North Pond', transaction_count: 5, income: 150000, expenses: 50000, profit: 100000 },
  ],
};

export const financialAnalytics = {
  source_breakdown: [{ label: 'Manual', total: 30000 }],
  monthly_trend: financialDashboard.monthly_trend,
  top_expenses: [{ name: 'Feed', total: 70000 }],
  top_income: [{ name: 'Fish Sales', total: 250000 }],
};
