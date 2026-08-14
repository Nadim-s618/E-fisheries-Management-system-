import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FinancialManagement from './FinancialManagement';
import {
  createFinancialBudget,
  createFinancialTransaction,
  getExpenseCategories,
  getFinancialAnalytics,
  getFinancialBudgets,
  getFinancialDashboard,
  getFinancialProfitLoss,
  getFinancialTransactions,
  getIncomeCategories,
  getPondFinancialPerformance,
  getPonds,
} from '../../test/mocks/financialApi';
import {
  expenseCategories,
  financialAnalytics,
  financialBudgets,
  financialDashboard,
  financialPonds,
  financialTransactions,
  incomeCategories,
  pondPerformance,
  profitLoss,
} from '../../test/mocks/financialData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/financialApi'));

describe('FinancialManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(financialPonds);
    getExpenseCategories.mockResolvedValue(expenseCategories);
    getIncomeCategories.mockResolvedValue(incomeCategories);
    getFinancialDashboard.mockResolvedValue(financialDashboard);
    getFinancialTransactions.mockResolvedValue(financialTransactions);
    getFinancialBudgets.mockResolvedValue(financialBudgets);
    getFinancialProfitLoss.mockResolvedValue(profitLoss);
    getPondFinancialPerformance.mockResolvedValue(pondPerformance);
    getFinancialAnalytics.mockResolvedValue(financialAnalytics);
    createFinancialTransaction.mockResolvedValue({});
    createFinancialBudget.mockResolvedValue({});
  });

  it('loads and displays the financial dashboard summary', async () => {
    renderWithProviders(<FinancialManagement />);

    expect(await screen.findByRole('heading', { name: 'Financial Dashboard' }))
      .toBeInTheDocument();
    expect(screen.getAllByText(/250,000/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/100,000/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/150,000/).length).toBeGreaterThan(0);
    expect(screen.getByText('Feed purchase')).toBeInTheDocument();
    expect(screen.getByText('INV-001')).toBeInTheDocument();
  });

  it('submits a new expense with calculated quantity and unit price', async () => {
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Expenses' }));

    fireEvent.change(screen.getByRole('combobox', { name: 'Category' }), {
      target: { value: '11' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Title' }), {
      target: { value: 'New feed purchase' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Quantity' }), {
      target: { value: '10' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Unit' }), {
      target: { value: 'kg' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Unit Price' }), {
      target: { value: '135' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save Expense' }));

    await waitFor(() => expect(createFinancialTransaction).toHaveBeenCalledWith(
      expect.objectContaining({
        transaction_type: 'expense',
        expense_category: 11,
        title: 'New feed purchase',
        amount: 1350,
        quantity: 10,
        unit: 'kg',
        unit_price: 135,
      }),
    ));
  });

  it('submits a new budget', async () => {
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Budgets' }));

    fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), {
      target: { value: 'Summer Feed Budget' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Amount' }), {
      target: { value: '90000' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save Budget' }));

    await waitFor(() => expect(createFinancialBudget).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Summer Feed Budget',
        amount: 90000,
        period_type: 'monthly',
        pond: null,
        expense_category: null,
      }),
    ));
  });

  it('renders profit and loss metrics', async () => {
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Profit & Loss' }));

    expect(screen.getByText('Total Income')).toBeInTheDocument();
    expect(screen.getByText('Net Profit')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getAllByText(/150,000/).length).toBeGreaterThan(0);
  });

  it('renders pond financial performance', async () => {
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Pond Performance' }));

    expect(screen.getByText('Profit by Pond')).toBeInTheDocument();
    expect(screen.getAllByText('North Pond').length).toBeGreaterThan(1);
    expect(screen.getByText('5 records')).toBeInTheDocument();
    expect(screen.getAllByText(/100,000/).length).toBeGreaterThan(0);
  });

  it('shows an error when saving an expense fails', async () => {
    createFinancialTransaction.mockRejectedValueOnce(new Error('Transaction could not be saved'));
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Expenses' }));
    fireEvent.change(screen.getByRole('combobox', { name: 'Category' }), { target: { value: '11' } });
    fireEvent.change(screen.getByRole('textbox', { name: 'Title' }), { target: { value: 'Failed expense' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Extra Expense' }), { target: { value: '100' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Expense' }));

    expect(await screen.findByText('Transaction could not be saved')).toBeInTheDocument();
  });
});
