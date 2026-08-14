import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FishHealthManagement from '../components/fish_health/FishHealthManagement';
import { createHealthRecord, getFishHealthDashboard, getPondStocks, getPonds } from '../test/mocks/fishHealthApi';
import { fishHealthDashboard, fishHealthPonds, fishStocks, healthRecord } from '../test/mocks/fishHealthData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/fishHealthApi'));

describe('fish health integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(fishHealthPonds);
    getPondStocks.mockResolvedValue(fishStocks);
    getFishHealthDashboard.mockResolvedValue(fishHealthDashboard);
    createHealthRecord.mockResolvedValue(healthRecord);
  });

  it('moves from health dashboard to diagnosis and saves a record', async () => {
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Diagnosis Form' }));
    await screen.findByRole('option', { name: /Tilapia Batch A/ });
    fireEvent.change(screen.getByRole('combobox', { name: 'Fish Stock' }), { target: { value: '101' } });
    fireEvent.click(screen.getByRole('checkbox', { name: 'white spots' }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Affected Count' }), { target: { value: '20' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save and Diagnose' }));

    await waitFor(() => expect(createHealthRecord).toHaveBeenCalledWith(expect.objectContaining({
      pond: 1, fish_stock: 101, symptoms: ['white spots'], affected_count: 20,
    })));
  });

  it('shows a diagnosis error when saving fails', async () => {
    createHealthRecord.mockRejectedValueOnce(new Error('Diagnosis service unavailable'));
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Diagnosis Form' }));
    await screen.findByRole('option', { name: /Tilapia Batch A/ });
    fireEvent.change(screen.getByRole('combobox', { name: 'Fish Stock' }), { target: { value: '101' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save and Diagnose' }));
    expect(await screen.findByText('Diagnosis service unavailable')).toBeInTheDocument();
  });
});
