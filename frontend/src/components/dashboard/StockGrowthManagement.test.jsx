import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { StockGrowthManagement } from './StockGrowthManagement';
import { createGrowthRecord, createStock, getPondStocks, getPonds } from '../../test/mocks/stockGrowthApi';
import { growthRecord, stockBatch, stockGrowthPonds } from '../../test/mocks/stockGrowthData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/stockGrowthApi'));

describe('StockGrowthManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(stockGrowthPonds);
    getPondStocks.mockResolvedValue([stockBatch]);
    createStock.mockResolvedValue(stockBatch);
    createGrowthRecord.mockResolvedValue(growthRecord);
  });

  it('loads a stock batch and saves a growth record', async () => {
    renderWithProviders(<StockGrowthManagement />);
    fireEvent.click(await screen.findByRole('button', { name: /North Pond/ }));
    expect(await screen.findByText('Tilapia Batch A')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Add growth' }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Sample count' }), { target: { value: '20' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Avg weight (g)' }), { target: { value: '32' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save growth' }));
    await waitFor(() => expect(createGrowthRecord).toHaveBeenCalledWith(21, expect.objectContaining({ sample_count: 20, mortality_count: 0 })));
  });

  it('shows an empty state when the selected pond has no stock batches', async () => {
    getPondStocks.mockResolvedValueOnce([]);
    renderWithProviders(<StockGrowthManagement />);
    fireEvent.click(await screen.findByRole('button', { name: /North Pond/ }));
    expect(await screen.findByText('No stock batches recorded for this pond yet.')).toBeInTheDocument();
    expect(createStock).not.toHaveBeenCalled();
  });
});
