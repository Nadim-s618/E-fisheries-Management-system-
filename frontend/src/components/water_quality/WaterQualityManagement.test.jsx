import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import WaterQualityManagement from './WaterQualityManagement';
import {
  compareWaterQualityPonds,
  createWaterQualityReading,
  getPonds,
  getWaterQualityDashboard,
  getWaterQualityGraph,
  getWaterQualityHistory,
  getWaterQualityReadings,
} from '../../test/mocks/waterQualityApi';
import {
  waterQualityComparison,
  waterQualityDashboard,
  waterQualityHistory,
  waterQualityPonds,
  waterQualityReadings,
} from '../../test/mocks/waterQualityData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/waterQualityApi'));

describe('WaterQualityManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(waterQualityPonds);
    getWaterQualityDashboard.mockResolvedValue(waterQualityDashboard);
    getWaterQualityHistory.mockResolvedValue(waterQualityHistory);
    getWaterQualityGraph.mockResolvedValue(waterQualityHistory);
    getWaterQualityReadings.mockResolvedValue(waterQualityReadings);
    createWaterQualityReading.mockResolvedValue({});
    compareWaterQualityPonds.mockResolvedValue(waterQualityComparison);
  });

  it('loads the dashboard and displays water quality summaries', async () => {
    renderWithProviders(<WaterQualityManagement />);

    expect(await screen.findByRole('heading', { name: 'Water Quality Management' })).toBeInTheDocument();
    expect(await screen.findByText('Overall Status')).toBeInTheDocument();
    expect(screen.getAllByText('Warning').length).toBeGreaterThan(0);
    expect(screen.getByText('28 °C')).toBeInTheDocument();
    expect(getWaterQualityDashboard).toHaveBeenCalledWith('1');
  });

  it('submits a new reading with numeric values', async () => {
    const onNotificationChange = vi.fn();
    renderWithProviders(<WaterQualityManagement onNotificationChange={onNotificationChange} />);
    await screen.findByRole('heading', { name: 'Water Quality Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Add Reading' }));

    const values = {
      'Temperature (°C)': '28',
      pH: '7.5',
      'DO (mg/L)': '6',
      'Ammonia (mg/L)': '0.1',
      'Nitrite (mg/L)': '0.05',
      'Nitrate (mg/L)': '10',
      'Turbidity (NTU)': '3',
      'Water Level (ft)': '5',
    };
    Object.entries(values).forEach(([label, value]) => {
      fireEvent.change(screen.getByRole('spinbutton', { name: label }), { target: { value } });
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save Reading' }));

    await waitFor(() => expect(createWaterQualityReading).toHaveBeenCalledWith(expect.objectContaining({
      pond: 1,
      temperature: 28,
      ph: 7.5,
      dissolved_oxygen: 6,
      salinity: null,
    })));
    expect(onNotificationChange).toHaveBeenCalledTimes(1);
  });

  it('loads history, graph data, and applies the period filter', async () => {
    renderWithProviders(<WaterQualityManagement />);
    await screen.findByRole('heading', { name: 'Water Quality Management' });
    fireEvent.click(screen.getByRole('button', { name: 'History' }));

    expect(await screen.findByRole('img', { name: 'Temperature historical chart' })).toBeInTheDocument();
    expect(screen.getAllByText('North Pond').length).toBeGreaterThan(0);
    expect(getWaterQualityHistory).toHaveBeenCalledWith({ pond: '1', period: 'daily' });
    expect(getWaterQualityGraph).toHaveBeenCalledWith({ pond: '1', period: 'daily' });
    expect(getWaterQualityReadings).toHaveBeenCalledWith({ pond: '1', date: '', status: '' });

    fireEvent.change(screen.getByRole('combobox', { name: 'Period' }), { target: { value: 'weekly' } });
    await waitFor(() => expect(getWaterQualityHistory).toHaveBeenLastCalledWith({ pond: '1', period: 'weekly' }));
  });

  it('compares the selected ponds', async () => {
    renderWithProviders(<WaterQualityManagement />);
    await screen.findByRole('heading', { name: 'Water Quality Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Comparison' }));
    fireEvent.click(screen.getByRole('button', { name: 'Compare Ponds' }));

    expect(await screen.findByText('Rank #1')).toBeInTheDocument();
    expect(screen.getAllByText('North Pond').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Avg Temp').length).toBeGreaterThan(0);
    expect(compareWaterQualityPonds).toHaveBeenCalledWith(['1', '2']);
  });

  it('shows AI recommendations and danger solutions', async () => {
    renderWithProviders(<WaterQualityManagement />);
    await screen.findByRole('heading', { name: 'Water Quality Management' });
    fireEvent.click(screen.getByRole('button', { name: 'AI Advisor' }));

    expect(await screen.findByRole('heading', { name: 'Water Quality Recommendations' })).toBeInTheDocument();
    expect(screen.getByText('Improve water quality before the next feeding.')).toBeInTheDocument();
    expect(screen.getByText('Danger parameter solutions')).toBeInTheDocument();
    expect(screen.getByText('Replace part of the pond water.')).toBeInTheDocument();
  });

  it('shows an empty state when the user has no ponds', async () => {
    getPonds.mockResolvedValueOnce([]);
    renderWithProviders(<WaterQualityManagement />);

    expect(await screen.findByText('Add a pond before recording water quality readings.')).toBeInTheDocument();
    expect(getWaterQualityDashboard).not.toHaveBeenCalled();
  });
});
