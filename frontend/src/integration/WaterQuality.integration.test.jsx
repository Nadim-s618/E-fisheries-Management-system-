import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import WaterQualityManagement from '../components/water_quality/WaterQualityManagement';
import { createWaterQualityReading, getPonds, getWaterQualityDashboard } from '../test/mocks/waterQualityApi';
import { waterQualityDashboard, waterQualityPonds } from '../test/mocks/waterQualityData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/waterQualityApi'));

describe('water quality integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(waterQualityPonds);
    getWaterQualityDashboard.mockResolvedValue(waterQualityDashboard);
    createWaterQualityReading.mockResolvedValue({});
  });

  it('moves from dashboard to reading form and saves a reading', async () => {
    renderWithProviders(<WaterQualityManagement />);
    await screen.findByRole('heading', { name: 'Water Quality Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Add Reading' }));

    const pondSelectors = screen.getAllByRole('combobox', { name: 'Pond' });
    fireEvent.change(pondSelectors[1], { target: { value: '1' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Temperature (°C)' }), { target: { value: '28' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'pH' }), { target: { value: '7.5' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'DO (mg/L)' }), { target: { value: '6' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Ammonia (mg/L)' }), { target: { value: '0.1' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Nitrite (mg/L)' }), { target: { value: '0.05' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Nitrate (mg/L)' }), { target: { value: '10' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Turbidity (NTU)' }), { target: { value: '3' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Water Level (ft)' }), { target: { value: '5' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Reading' }));

    await waitFor(() => expect(createWaterQualityReading).toHaveBeenCalledWith(expect.objectContaining({
      pond: 1,
      temperature: 28,
      ph: 7.5,
      dissolved_oxygen: 6,
    })));
  });

  it('shows the empty state and skips dashboard loading without ponds', async () => {
    getPonds.mockResolvedValueOnce([]);
    renderWithProviders(<WaterQualityManagement />);
    expect(await screen.findByText('Add a pond before recording water quality readings.')).toBeInTheDocument();
    expect(getWaterQualityDashboard).not.toHaveBeenCalled();
  });
});
