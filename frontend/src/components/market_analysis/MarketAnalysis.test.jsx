import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import MarketAnalysis from './MarketAnalysis';
import { getMarketAnalysisDashboard } from '../../test/mocks/marketAnalysisApi';
import { marketAnalysisDashboard } from '../../test/mocks/marketAnalysisData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/marketAnalysisApi'));

describe('MarketAnalysis', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getMarketAnalysisDashboard.mockResolvedValue(marketAnalysisDashboard);
  });

  it('loads market summaries, records, and the selected market details', async () => {
    renderWithProviders(<MarketAnalysis />);

    expect(await screen.findByRole('heading', { name: 'Bangladesh Fish Price Dashboard' }))
      .toBeInTheDocument();
    expect(screen.getByText(/Source:.*Bangladesh Fish Market Authority/)).toBeInTheDocument();
    expect(screen.getByText('Market Points')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Rui in Dhaka')).toBeInTheDocument();
    expect(screen.getAllByText('BDT 220').length).toBeGreaterThan(0);
    expect(screen.getByText('Last 7 Days Price')).toBeInTheDocument();
    expect(screen.getByText('Future 7 Days Price Prediction')).toBeInTheDocument();
    expect(getMarketAnalysisDashboard).toHaveBeenCalledWith({ refresh: false });
  });

  it('filters records by division and fish', async () => {
    renderWithProviders(<MarketAnalysis />);
    await screen.findByText('Rui in Dhaka');

    fireEvent.change(screen.getByRole('combobox', { name: 'Division' }), {
      target: { value: 'Chattogram' },
    });
    expect(screen.getByRole('button', { name: 'Tilapia' })).toBeInTheDocument();
    expect(screen.queryByText('Rui in Dhaka')).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole('combobox', { name: 'Fish' }), {
      target: { value: 'Rui' },
    });
    expect(screen.getByText('No prices match these filters.')).toBeInTheDocument();
  });

  it('changes the selected market when a table row is clicked', async () => {
    renderWithProviders(<MarketAnalysis />);
    await screen.findByText('Rui in Dhaka');

    fireEvent.click(screen.getByRole('button', { name: 'Tilapia' }));

    expect(screen.getByText('Tilapia in Chattogram')).toBeInTheDocument();
    expect(screen.getAllByText('BDT 180').length).toBeGreaterThan(0);
    expect(screen.getAllByLabelText('Decrease').length).toBeGreaterThan(0);
  });

  it('requests fresh prices when refresh is clicked', async () => {
    renderWithProviders(<MarketAnalysis />);
    await screen.findByText('Rui in Dhaka');

    fireEvent.click(screen.getByRole('button', { name: /Refresh prices/ }));

    await waitFor(() => expect(getMarketAnalysisDashboard).toHaveBeenLastCalledWith({
      refresh: true,
    }));
  });

  it('shows an API error when market data cannot be loaded', async () => {
    getMarketAnalysisDashboard.mockRejectedValueOnce(new Error('Market service unavailable'));
    renderWithProviders(<MarketAnalysis />);

    expect(await screen.findByText('Market service unavailable')).toBeInTheDocument();
  });
});
