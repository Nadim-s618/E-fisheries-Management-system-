import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FinancialManagement from '../components/financials/FinancialManagement';
import { createFinancialTransaction, getExpenseCategories, getFinancialDashboard, getIncomeCategories, getPonds } from '../test/mocks/financialApi';
import { expenseCategories, financialDashboard, financialPonds, incomeCategories } from '../test/mocks/financialData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/financialApi'));

describe('financials integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(financialPonds);
    getExpenseCategories.mockResolvedValue(expenseCategories);
    getIncomeCategories.mockResolvedValue(incomeCategories);
    getFinancialDashboard.mockResolvedValue(financialDashboard);
    createFinancialTransaction.mockResolvedValue({});
  });

  it('moves from the dashboard to an expense and submits calculated totals', async () => {
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Expenses' }));
    fireEvent.change(screen.getByRole('combobox', { name: 'Category' }), { target: { value: '11' } });
    fireEvent.change(screen.getByRole('textbox', { name: 'Title' }), { target: { value: 'Feed purchase' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Quantity' }), { target: { value: '10' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Unit Price' }), { target: { value: '135' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Expense' }));

    await waitFor(() => expect(createFinancialTransaction).toHaveBeenCalledWith(expect.objectContaining({
      transaction_type: 'expense', amount: 1350, quantity: 10, unit_price: 135,
    })));
  });

  it('displays a save error when the transaction service fails', async () => {
    createFinancialTransaction.mockRejectedValueOnce(new Error('Transaction service unavailable'));
    renderWithProviders(<FinancialManagement />);
    await screen.findByRole('heading', { name: 'Financial Dashboard' });
    fireEvent.click(screen.getByRole('button', { name: 'Expenses' }));
    fireEvent.change(screen.getByRole('combobox', { name: 'Category' }), { target: { value: '11' } });
    fireEvent.change(screen.getByRole('textbox', { name: 'Title' }), { target: { value: 'Failed purchase' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Quantity' }), { target: { value: '1' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Unit Price' }), { target: { value: '100' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Expense' }));
    expect(await screen.findByText('Transaction service unavailable')).toBeInTheDocument();
  });
});
