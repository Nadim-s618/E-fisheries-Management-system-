import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  createAutomaticFinancialRecord,
  createFinancialBudget,
  createFinancialTransaction,
  estimateHarvestRevenue,
  getExpenseCategories,
  getFeedCostAnalysis,
  getFinancialAnalytics,
  getFinancialBudgets,
  getFinancialDashboard,
  getFinancialProfitLoss,
  getFinancialTransactions,
  getIncomeCategories,
  getPondFinancialPerformance,
  getPonds,
} from '../../lib/api';
import './FinancialManagement.css';

const TABS = [
  'Dashboard',
  'Expenses',
  'Income',
  'Automatic Records',
  'Profit & Loss',
  'Pond Performance',
  'Feed Costs',
  'Harvest Estimator',
  'Budgets',
  'Analytics',
];

const AUTO_SOURCES = [
  { value: 'feed_purchase', label: 'Feed Purchase', type: 'expense', unit: 'kg' },
  { value: 'fish_stocking', label: 'Fish Stocking', type: 'expense', unit: 'fish' },
  { value: 'medicine_treatment', label: 'Medicine Treatment', type: 'expense', unit: '' },
  { value: 'labor', label: 'Labor', type: 'expense', unit: 'day' },
  { value: 'harvest_sale', label: 'Harvest Sale', type: 'income', unit: 'kg' },
  { value: 'pond_maintenance', label: 'Pond Maintenance', type: 'expense', unit: '' },
  { value: 'equipment_purchase', label: 'Equipment Purchase', type: 'expense', unit: '' },
];

const EMPTY_TRANSACTION = {
  pond: '',
  transaction_type: 'expense',
  expense_category: '',
  income_category: '',
  title: '',
  description: '',
  amount: '',
  quantity: '',
  unit: '',
  unit_price: '',
  transaction_date: new Date().toISOString().slice(0, 10),
  reference: '',
};

const EMPTY_AUTO = {
  source_type: 'feed_purchase',
  pond: '',
  title: '',
  description: '',
  amount: '',
  quantity: '',
  unit: 'kg',
  unit_price: '',
  transaction_date: new Date().toISOString().slice(0, 10),
  reference: '',
};

const EMPTY_BUDGET = {
  pond: '',
  expense_category: '',
  name: '',
  amount: '',
  period_type: 'monthly',
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
  notes: '',
};

const EMPTY_ESTIMATE = {
  pond: '',
  estimated_weight_kg: '',
  expected_price_per_kg: '',
  estimated_harvest_cost: '',
};

function formatMoney(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'BDT',
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatNumber(value, suffix = '') {
  if (value === null || value === undefined || value === '') return '0';
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}`;
}

function formatDate(value) {
  if (!value) return 'No date';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value));
}

function PanelState({ type = 'empty', children }) {
  return <div className={`fm-state fm-state-${type}`}>{children}</div>;
}

function Metric({ label, value, tone = 'default', sub }) {
  return (
    <article className={`fm-metric fm-metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {sub && <small>{sub}</small>}
    </article>
  );
}

function MiniBars({ rows = [], valueKey = 'total', labelKey = 'name' }) {
  const topRows = rows.slice(0, 6);
  const max = Math.max(...topRows.map(row => Number(row[valueKey] || 0)), 1);

  if (!topRows.length) {
    return <PanelState>No chart data yet.</PanelState>;
  }

  return (
    <div className="fm-bars">
      {topRows.map(row => (
        <div key={`${row[labelKey]}-${row[valueKey]}`} className="fm-bar-row">
          <span>{row[labelKey] || row.category || row.label}</span>
          <div><i style={{ width: `${Math.max((Number(row[valueKey] || 0) / max) * 100, 4)}%` }} /></div>
          <strong>{formatMoney(row[valueKey])}</strong>
        </div>
      ))}
    </div>
  );
}

function TrendChart({ rows = [] }) {
  const values = rows.flatMap(row => [Number(row.income || 0), Number(row.expenses || 0)]);
  const max = Math.max(...values, 1);

  if (!rows.length) {
    return <PanelState>No monthly records yet.</PanelState>;
  }

  return (
    <div className="fm-trend" aria-label="Monthly income and expenses chart">
      {rows.slice(-8).map(row => (
        <div key={row.month} className="fm-trend-col">
          <div className="fm-trend-bars">
            <i className="income" style={{ height: `${Math.max((Number(row.income || 0) / max) * 100, 5)}%` }} />
            <i className="expense" style={{ height: `${Math.max((Number(row.expenses || 0) / max) * 100, 5)}%` }} />
          </div>
          <span>{String(row.month).slice(0, 7)}</span>
        </div>
      ))}
    </div>
  );
}

function TransactionTable({ rows, loading, error }) {
  if (loading) return <PanelState>Loading financial records...</PanelState>;
  if (error) return <PanelState type="error">{error}</PanelState>;
  if (!rows.length) return <PanelState>No transactions match this view.</PanelState>;

  return (
    <div className="fm-table-wrap">
      <table className="fm-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Title</th>
            <th>Pond</th>
            <th>Category</th>
            <th>Source</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.id}>
              <td>{formatDate(row.transaction_date)}</td>
              <td>
                <strong>{row.title}</strong>
                {row.reference && <small>{row.reference}</small>}
              </td>
              <td>{row.pond_name || 'All ponds'}</td>
              <td>{row.expense_category_name || row.income_category_name || 'Uncategorized'}</td>
              <td>{row.is_automatic ? row.source_type_display : 'Manual'}</td>
              <td className={row.transaction_type === 'income' ? 'fm-positive' : 'fm-negative'}>
                {row.transaction_type === 'income' ? '+' : '-'}{formatMoney(row.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TransactionForm({ type, ponds, expenseCategories, incomeCategories, onSaved }) {
  const [formData, setFormData] = useState({ ...EMPTY_TRANSACTION, transaction_type: type });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const categories = type === 'income' ? incomeCategories : expenseCategories;

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      const payload = {
        pond: formData.pond ? Number(formData.pond) : null,
        transaction_type: type,
        expense_category: type === 'expense' ? Number(formData.expense_category) : null,
        income_category: type === 'income' ? Number(formData.income_category) : null,
        title: formData.title,
        description: formData.description,
        amount: Number(formData.amount),
        quantity: formData.quantity ? Number(formData.quantity) : null,
        unit: formData.unit,
        unit_price: formData.unit_price ? Number(formData.unit_price) : null,
        transaction_date: formData.transaction_date,
        reference: formData.reference,
      };
      await createFinancialTransaction(payload);
      setFormData({ ...EMPTY_TRANSACTION, transaction_type: type });
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="fm-panel fm-form" onSubmit={handleSubmit}>
      <div className="fm-panel-header">
        <div>
          <span>{type === 'income' ? 'Income Management' : 'Expense Management'}</span>
          <h2>{type === 'income' ? 'Add Income' : 'Add Expense'}</h2>
        </div>
      </div>

      <div className="fm-form-grid">
        <label className="fm-field">
          <span>Pond</span>
          <select name="pond" value={formData.pond} onChange={handleChange}>
            <option value="">All ponds</option>
            {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
          </select>
        </label>
        <label className="fm-field">
          <span>Category</span>
          <select
            name={type === 'income' ? 'income_category' : 'expense_category'}
            value={type === 'income' ? formData.income_category : formData.expense_category}
            onChange={handleChange}
            required
          >
            <option value="">Select category</option>
            {categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </label>
        <label className="fm-field">
          <span>Title</span>
          <input name="title" value={formData.title} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Amount</span>
          <input name="amount" type="number" min="0" step="0.01" value={formData.amount} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Date</span>
          <input name="transaction_date" type="date" value={formData.transaction_date} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Quantity</span>
          <input name="quantity" type="number" min="0" step="0.01" value={formData.quantity} onChange={handleChange} />
        </label>
        <label className="fm-field">
          <span>Unit</span>
          <input name="unit" value={formData.unit} onChange={handleChange} placeholder="kg, fish, day" />
        </label>
        <label className="fm-field">
          <span>Unit Price</span>
          <input name="unit_price" type="number" min="0" step="0.01" value={formData.unit_price} onChange={handleChange} />
        </label>
        <label className="fm-field">
          <span>Reference</span>
          <input name="reference" value={formData.reference} onChange={handleChange} />
        </label>
        <label className="fm-field fm-field-wide">
          <span>Description</span>
          <textarea name="description" value={formData.description} onChange={handleChange} rows="3" />
        </label>
      </div>

      {error && <PanelState type="error">{error}</PanelState>}

      <div className="fm-actions">
        <button type="button" className="fm-btn fm-btn-secondary" onClick={() => setFormData({ ...EMPTY_TRANSACTION, transaction_type: type })}>
          Clear
        </button>
        <button type="submit" className="fm-btn fm-btn-primary" disabled={saving}>
          {saving ? 'Saving...' : `Save ${type === 'income' ? 'Income' : 'Expense'}`}
        </button>
      </div>
    </form>
  );
}

function AutomaticRecordForm({ ponds, onSaved }) {
  const [formData, setFormData] = useState(EMPTY_AUTO);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const source = AUTO_SOURCES.find(item => item.value === formData.source_type) || AUTO_SOURCES[0];

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  function handleSourceChange(event) {
    const nextSource = AUTO_SOURCES.find(item => item.value === event.target.value);
    setFormData(current => ({
      ...current,
      source_type: event.target.value,
      unit: nextSource?.unit || '',
      title: '',
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      await createAutomaticFinancialRecord({
        ...formData,
        pond: formData.pond ? Number(formData.pond) : null,
        amount: Number(formData.amount),
        quantity: formData.quantity ? Number(formData.quantity) : null,
        unit_price: formData.unit_price ? Number(formData.unit_price) : null,
      });
      setFormData(EMPTY_AUTO);
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="fm-panel fm-form" onSubmit={handleSubmit}>
      <div className="fm-panel-header">
        <div>
          <span>Automatic Financial Records</span>
          <h2>Create From Farm Event</h2>
        </div>
        <strong className={`fm-chip fm-chip-${source.type}`}>{source.type}</strong>
      </div>

      <div className="fm-form-grid">
        <label className="fm-field">
          <span>Event</span>
          <select name="source_type" value={formData.source_type} onChange={handleSourceChange}>
            {AUTO_SOURCES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
        <label className="fm-field">
          <span>Pond</span>
          <select name="pond" value={formData.pond} onChange={handleChange}>
            <option value="">All ponds</option>
            {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
          </select>
        </label>
        <label className="fm-field">
          <span>Title</span>
          <input name="title" value={formData.title} onChange={handleChange} placeholder={source.label} />
        </label>
        <label className="fm-field">
          <span>Amount</span>
          <input name="amount" type="number" min="0" step="0.01" value={formData.amount} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Quantity</span>
          <input name="quantity" type="number" min="0" step="0.01" value={formData.quantity} onChange={handleChange} />
        </label>
        <label className="fm-field">
          <span>Unit</span>
          <input name="unit" value={formData.unit} onChange={handleChange} />
        </label>
        <label className="fm-field">
          <span>Unit Price</span>
          <input name="unit_price" type="number" min="0" step="0.01" value={formData.unit_price} onChange={handleChange} />
        </label>
        <label className="fm-field">
          <span>Date</span>
          <input name="transaction_date" type="date" value={formData.transaction_date} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Reference</span>
          <input name="reference" value={formData.reference} onChange={handleChange} />
        </label>
        <label className="fm-field fm-field-wide">
          <span>Description</span>
          <textarea name="description" value={formData.description} onChange={handleChange} rows="3" />
        </label>
      </div>

      {error && <PanelState type="error">{error}</PanelState>}

      <div className="fm-actions">
        <button type="submit" className="fm-btn fm-btn-primary" disabled={saving}>
          {saving ? 'Creating...' : 'Create Automatic Record'}
        </button>
      </div>
    </form>
  );
}

function BudgetForm({ ponds, expenseCategories, onSaved }) {
  const [formData, setFormData] = useState(EMPTY_BUDGET);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      await createFinancialBudget({
        ...formData,
        pond: formData.pond ? Number(formData.pond) : null,
        expense_category: formData.expense_category ? Number(formData.expense_category) : null,
        amount: Number(formData.amount),
        end_date: formData.end_date || null,
      });
      setFormData(EMPTY_BUDGET);
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="fm-panel fm-form" onSubmit={handleSubmit}>
      <div className="fm-panel-header">
        <div>
          <span>Budget Management</span>
          <h2>Monthly or Pond Budget</h2>
        </div>
      </div>

      <div className="fm-form-grid">
        <label className="fm-field">
          <span>Name</span>
          <input name="name" value={formData.name} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Amount</span>
          <input name="amount" type="number" min="0" step="0.01" value={formData.amount} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>Period</span>
          <select name="period_type" value={formData.period_type} onChange={handleChange}>
            <option value="monthly">Monthly</option>
            <option value="pond_cycle">Pond Cycle</option>
          </select>
        </label>
        <label className="fm-field">
          <span>Pond</span>
          <select name="pond" value={formData.pond} onChange={handleChange}>
            <option value="">All ponds</option>
            {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
          </select>
        </label>
        <label className="fm-field">
          <span>Category</span>
          <select name="expense_category" value={formData.expense_category} onChange={handleChange}>
            <option value="">All expense categories</option>
            {expenseCategories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </label>
        <label className="fm-field">
          <span>Start Date</span>
          <input name="start_date" type="date" value={formData.start_date} onChange={handleChange} required />
        </label>
        <label className="fm-field">
          <span>End Date</span>
          <input name="end_date" type="date" value={formData.end_date} onChange={handleChange} />
        </label>
        <label className="fm-field fm-field-wide">
          <span>Notes</span>
          <textarea name="notes" value={formData.notes} onChange={handleChange} rows="3" />
        </label>
      </div>

      {error && <PanelState type="error">{error}</PanelState>}

      <div className="fm-actions">
        <button type="submit" className="fm-btn fm-btn-primary" disabled={saving}>
          {saving ? 'Saving...' : 'Save Budget'}
        </button>
      </div>
    </form>
  );
}

function BudgetList({ budgets }) {
  if (!budgets.length) return <PanelState>No budgets yet.</PanelState>;

  return (
    <div className="fm-budget-list">
      {budgets.map(budget => (
        <article key={budget.id} className="fm-budget-card">
          <div className="fm-card-top">
            <div>
              <span>{budget.period_type.replace('_', ' ')}</span>
              <h3>{budget.name}</h3>
            </div>
            <strong>{formatMoney(budget.amount)}</strong>
          </div>
          <div className="fm-progress"><i style={{ width: `${Math.min(Number(budget.used_percent || 0), 100)}%` }} /></div>
          <dl>
            <div><dt>Actual</dt><dd>{formatMoney(budget.actual_spend)}</dd></div>
            <div><dt>Remaining</dt><dd>{formatMoney(budget.remaining)}</dd></div>
            <div><dt>Scope</dt><dd>{budget.pond_name || 'All ponds'} · {budget.expense_category_name || 'All categories'}</dd></div>
          </dl>
        </article>
      ))}
    </div>
  );
}

function HarvestEstimator({ ponds }) {
  const [formData, setFormData] = useState(EMPTY_ESTIMATE);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormData(current => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');

    try {
      const data = await estimateHarvestRevenue({
        pond: formData.pond ? Number(formData.pond) : null,
        estimated_weight_kg: Number(formData.estimated_weight_kg),
        expected_price_per_kg: Number(formData.expected_price_per_kg),
        estimated_harvest_cost: Number(formData.estimated_harvest_cost || 0),
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fm-grid-two">
      <form className="fm-panel fm-form" onSubmit={handleSubmit}>
        <div className="fm-panel-header">
          <div>
            <span>Harvest Revenue Estimator</span>
            <h2>Estimate Sale Result</h2>
          </div>
        </div>
        <div className="fm-form-grid fm-form-grid-compact">
          <label className="fm-field">
            <span>Pond</span>
            <select name="pond" value={formData.pond} onChange={handleChange}>
              <option value="">No pond cost history</option>
              {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
            </select>
          </label>
          <label className="fm-field">
            <span>Weight kg</span>
            <input name="estimated_weight_kg" type="number" min="0" step="0.01" value={formData.estimated_weight_kg} onChange={handleChange} required />
          </label>
          <label className="fm-field">
            <span>Price per kg</span>
            <input name="expected_price_per_kg" type="number" min="0" step="0.01" value={formData.expected_price_per_kg} onChange={handleChange} required />
          </label>
          <label className="fm-field">
            <span>Harvest Cost</span>
            <input name="estimated_harvest_cost" type="number" min="0" step="0.01" value={formData.estimated_harvest_cost} onChange={handleChange} />
          </label>
        </div>
        {error && <PanelState type="error">{error}</PanelState>}
        <div className="fm-actions">
          <button type="submit" className="fm-btn fm-btn-primary" disabled={saving}>
            {saving ? 'Estimating...' : 'Estimate Revenue'}
          </button>
        </div>
      </form>

      <section className="fm-panel">
        <div className="fm-panel-header">
          <div>
            <span>Projection</span>
            <h2>Expected Result</h2>
          </div>
        </div>
        {!result ? (
          <PanelState>Enter harvest values to calculate projected revenue and profit.</PanelState>
        ) : (
          <div className="fm-overview fm-overview-small">
            <Metric label="Gross Revenue" value={formatMoney(result.gross_revenue)} tone="income" />
            <Metric label="Pond Cost" value={formatMoney(result.historical_pond_cost)} tone="expense" />
            <Metric label="Projected Profit" value={formatMoney(result.projected_profit)} tone={Number(result.projected_profit) >= 0 ? 'income' : 'expense'} />
            <Metric label="Margin" value={`${formatNumber(result.projected_margin_percent)}%`} />
          </div>
        )}
      </section>
    </div>
  );
}

export default function FinancialManagement() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [ponds, setPonds] = useState([]);
  const [selectedPondId, setSelectedPondId] = useState('');
  const [expenseCategories, setExpenseCategories] = useState([]);
  const [incomeCategories, setIncomeCategories] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [profitLoss, setProfitLoss] = useState(null);
  const [pondPerformance, setPondPerformance] = useState([]);
  const [feedAnalysis, setFeedAnalysis] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const filters = useMemo(() => (
    selectedPondId ? { pond: selectedPondId } : {}
  ), [selectedPondId]);

  const loadBase = useCallback(async () => {
    try {
      const [pondList, expenseList, incomeList] = await Promise.all([
        getPonds(),
        getExpenseCategories(),
        getIncomeCategories(),
      ]);
      setPonds(pondList || []);
      setExpenseCategories(expenseList || []);
      setIncomeCategories(incomeList || []);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const loadFinancials = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const [
        dashboardData,
        transactionRows,
        budgetRows,
        profitLossData,
        performanceData,
        feedData,
        analyticsData,
      ] = await Promise.all([
        getFinancialDashboard(filters),
        getFinancialTransactions(filters),
        getFinancialBudgets({ active: 'true', ...filters }),
        getFinancialProfitLoss(filters),
        getPondFinancialPerformance(filters),
        getFeedCostAnalysis(filters),
        getFinancialAnalytics(filters),
      ]);

      setDashboard(dashboardData);
      setTransactions(transactionRows || []);
      setBudgets(budgetRows || []);
      setProfitLoss(profitLossData);
      setPondPerformance(performanceData?.ponds || []);
      setFeedAnalysis(feedData);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadBase();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [loadBase]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadFinancials();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [loadFinancials, refreshKey]);

  function refresh() {
    setRefreshKey(current => current + 1);
  }

  const summary = dashboard?.summary || {};
  const visibleTransactions = useMemo(() => {
    if (activeTab === 'Expenses') return transactions.filter(row => row.transaction_type === 'expense');
    if (activeTab === 'Income') return transactions.filter(row => row.transaction_type === 'income');
    return transactions;
  }, [activeTab, transactions]);

  return (
    <section className="fm-root" aria-labelledby="financials-title">
      <div className="fm-header">
        <div>
          <span>Financials</span>
          <h1 id="financials-title">Financial Dashboard</h1>
        </div>
        <div className="fm-header-actions">
          <label className="fm-field fm-pond-picker">
            <span>Pond</span>
            <select value={selectedPondId} onChange={event => setSelectedPondId(event.target.value)}>
              <option value="">All ponds</option>
              {ponds.map(pond => <option key={pond.id} value={pond.id}>{pond.name}</option>)}
            </select>
          </label>
          <button type="button" className="fm-btn fm-btn-secondary" onClick={refresh}>Refresh</button>
        </div>
      </div>

      <div className="fm-tabs" role="tablist" aria-label="Financial views">
        {TABS.map(tab => (
          <button key={tab} type="button" className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>
            {tab}
          </button>
        ))}
      </div>

      {error && <PanelState type="error">{error}</PanelState>}

      {activeTab === 'Dashboard' && (
        <div className="fm-stack">
          <div className="fm-overview">
            <Metric label="Income" value={formatMoney(summary.income)} tone="income" />
            <Metric label="Expenses" value={formatMoney(summary.expenses)} tone="expense" />
            <Metric label="Profit" value={formatMoney(summary.profit)} tone={Number(summary.profit || 0) >= 0 ? 'income' : 'expense'} />
            <Metric label="Auto Records" value={summary.automatic_record_count || 0} />
            <Metric label="Active Budgets" value={summary.active_budget_count || 0} />
            <Metric label="Over Budget" value={summary.over_budget_count || 0} tone="warning" />
          </div>

          <div className="fm-grid-two">
            <section className="fm-panel">
              <div className="fm-panel-header"><div><span>Charts</span><h2>Monthly Trend</h2></div></div>
              <TrendChart rows={dashboard?.monthly_trend || []} />
            </section>
            <section className="fm-panel">
              <div className="fm-panel-header"><div><span>Analytics</span><h2>Expense Breakdown</h2></div></div>
              <MiniBars rows={dashboard?.expense_breakdown || []} valueKey="total" labelKey="category" />
            </section>
          </div>

          <section className="fm-panel">
            <div className="fm-panel-header"><div><span>Recent</span><h2>Latest Records</h2></div></div>
            <TransactionTable rows={dashboard?.recent_transactions || []} loading={loading} error="" />
          </section>
        </div>
      )}

      {activeTab === 'Expenses' && (
        <div className="fm-stack">
          <TransactionForm type="expense" ponds={ponds} expenseCategories={expenseCategories} incomeCategories={incomeCategories} onSaved={refresh} />
          <TransactionTable rows={visibleTransactions} loading={loading} error="" />
        </div>
      )}

      {activeTab === 'Income' && (
        <div className="fm-stack">
          <TransactionForm type="income" ponds={ponds} expenseCategories={expenseCategories} incomeCategories={incomeCategories} onSaved={refresh} />
          <TransactionTable rows={visibleTransactions} loading={loading} error="" />
        </div>
      )}

      {activeTab === 'Automatic Records' && (
        <div className="fm-stack">
          <AutomaticRecordForm ponds={ponds} onSaved={refresh} />
          <TransactionTable rows={transactions.filter(row => row.is_automatic)} loading={loading} error="" />
        </div>
      )}

      {activeTab === 'Profit & Loss' && (
        <div className="fm-stack">
          <div className="fm-overview">
            <Metric label="Total Income" value={formatMoney(profitLoss?.income)} tone="income" />
            <Metric label="Total Expenses" value={formatMoney(profitLoss?.expenses)} tone="expense" />
            <Metric label="Net Profit" value={formatMoney(profitLoss?.net_profit)} tone={Number(profitLoss?.net_profit || 0) >= 0 ? 'income' : 'expense'} />
            <Metric label="Margin" value={`${formatNumber(profitLoss?.profit_margin_percent)}%`} />
          </div>
          <div className="fm-grid-two">
            <section className="fm-panel">
              <div className="fm-panel-header"><div><span>P&L</span><h2>Income Categories</h2></div></div>
              <MiniBars rows={profitLoss?.income_breakdown || []} />
            </section>
            <section className="fm-panel">
              <div className="fm-panel-header"><div><span>P&L</span><h2>Expense Categories</h2></div></div>
              <MiniBars rows={profitLoss?.expense_breakdown || []} />
            </section>
          </div>
        </div>
      )}

      {activeTab === 'Pond Performance' && (
        <section className="fm-panel">
          <div className="fm-panel-header"><div><span>Pond-wise Performance</span><h2>Profit by Pond</h2></div></div>
          <div className="fm-performance-grid">
            {pondPerformance.map(row => (
              <article key={row.pond_id} className="fm-performance-card">
                <div className="fm-card-top">
                  <div><span>{row.transaction_count} records</span><h3>{row.pond_name}</h3></div>
                  <strong className={Number(row.profit) >= 0 ? 'fm-positive' : 'fm-negative'}>{formatMoney(row.profit)}</strong>
                </div>
                <dl>
                  <div><dt>Income</dt><dd>{formatMoney(row.income)}</dd></div>
                  <div><dt>Expenses</dt><dd>{formatMoney(row.expenses)}</dd></div>
                  <div><dt>Feed Cost</dt><dd>{formatMoney(row.feed_cost)}</dd></div>
                  <div><dt>Harvest</dt><dd>{formatMoney(row.harvest_revenue)}</dd></div>
                </dl>
              </article>
            ))}
          </div>
          {!pondPerformance.length && <PanelState>No pond financial records yet.</PanelState>}
        </section>
      )}

      {activeTab === 'Feed Costs' && (
        <div className="fm-stack">
          <div className="fm-overview fm-overview-small">
            <Metric label="Feed Cost" value={formatMoney(feedAnalysis?.summary?.total_feed_cost)} tone="expense" />
            <Metric label="Feed Quantity" value={formatNumber(feedAnalysis?.summary?.total_feed_quantity)} />
            <Metric label="Avg Cost/Unit" value={formatMoney(feedAnalysis?.summary?.average_cost_per_unit)} />
            <Metric label="Records" value={feedAnalysis?.summary?.record_count || 0} />
          </div>
          <section className="fm-panel">
            <div className="fm-panel-header"><div><span>Feed Cost Analysis</span><h2>Pond Feed Costs</h2></div></div>
            <MiniBars rows={feedAnalysis?.ponds || []} valueKey="total_cost" labelKey="pond_name" />
          </section>
        </div>
      )}

      {activeTab === 'Harvest Estimator' && <HarvestEstimator ponds={ponds} />}

      {activeTab === 'Budgets' && (
        <div className="fm-stack">
          <BudgetForm ponds={ponds} expenseCategories={expenseCategories} onSaved={refresh} />
          <BudgetList budgets={budgets} />
        </div>
      )}

      {activeTab === 'Analytics' && (
        <div className="fm-grid-two">
          <section className="fm-panel">
            <div className="fm-panel-header"><div><span>Charts & Analytics</span><h2>Source Breakdown</h2></div></div>
            <MiniBars rows={analytics?.source_breakdown || []} valueKey="total" labelKey="label" />
          </section>
          <section className="fm-panel">
            <div className="fm-panel-header"><div><span>Charts & Analytics</span><h2>Monthly Trend</h2></div></div>
            <TrendChart rows={analytics?.monthly_trend || []} />
          </section>
          <section className="fm-panel">
            <div className="fm-panel-header"><div><span>Charts & Analytics</span><h2>Top Expenses</h2></div></div>
            <MiniBars rows={analytics?.top_expenses || []} />
          </section>
          <section className="fm-panel">
            <div className="fm-panel-header"><div><span>Charts & Analytics</span><h2>Top Income</h2></div></div>
            <MiniBars rows={analytics?.top_income || []} />
          </section>
        </div>
      )}
    </section>
  );
}
