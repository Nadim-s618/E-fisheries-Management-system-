import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FishHealthManagement from './FishHealthManagement';
import {
  addTreatmentTrackingEntry,
  createHealthRecord,
  createTreatmentPlan,
  getDiseaseLibrary,
  getFishHealthAlerts,
  getFishHealthDashboard,
  getFishHealthRecommendation,
  getHealthRecords,
  getPondStocks,
  getPonds,
  getTreatmentPlans,
  markFishHealthAlertsRead,
} from '../../test/mocks/fishHealthApi';
import {
  alerts,
  diseases,
  fishHealthDashboard,
  fishHealthPonds,
  fishStocks,
  healthRecord,
  recommendation,
  treatments,
} from '../../test/mocks/fishHealthData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/fishHealthApi'));

describe('FishHealthManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(fishHealthPonds);
    getPondStocks.mockResolvedValue(fishStocks);
    getFishHealthDashboard.mockResolvedValue(fishHealthDashboard);
    getHealthRecords.mockResolvedValue([healthRecord]);
    getDiseaseLibrary.mockResolvedValue(diseases);
    getTreatmentPlans.mockResolvedValue(treatments);
    getFishHealthRecommendation.mockResolvedValue(recommendation);
    getFishHealthAlerts.mockResolvedValue(alerts);
    createHealthRecord.mockResolvedValue(healthRecord);
    createTreatmentPlan.mockResolvedValue({});
    addTreatmentTrackingEntry.mockResolvedValue({});
    markFishHealthAlertsRead.mockResolvedValue({});
  });

  it('loads the fish health dashboard and displays summary data', async () => {
    renderWithProviders(<FishHealthManagement />);

    expect(await screen.findByRole('heading', { name: 'Fish Health Management' }))
      .toBeInTheDocument();
    expect(await screen.findByText('Active Cases')).toBeInTheDocument();
    expect(screen.getAllByText('Health Records').length).toBeGreaterThan(0);
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Active Cases')).toBeInTheDocument();
    expect(screen.getByText('Oxygen is below the preferred range')).toBeInTheDocument();
    expect(screen.getByText('Tilapia Batch A')).toBeInTheDocument();
  });

  it('submits a diagnosis with selected symptoms and fish stock', async () => {
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Diagnosis Form' }));
    await screen.findByRole('option', { name: /Tilapia Batch A/ });

    fireEvent.change(screen.getByRole('combobox', { name: 'Fish Stock' }), {
      target: { value: '101' },
    });
    fireEvent.click(screen.getByRole('checkbox', { name: 'white spots' }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Affected Count' }), {
      target: { value: '20' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Symptom Notes' }), {
      target: { value: 'White spots visible on the body.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save and Diagnose' }));

    await waitFor(() => expect(createHealthRecord).toHaveBeenCalledWith(
      expect.objectContaining({
        pond: 1,
        fish_stock: 101,
        species: 'Tilapia',
        symptoms: ['white spots'],
        affected_count: 20,
        mortality_count: 0,
      }),
    ));
  });

  it('renders the disease library', async () => {
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Disease Library' }));

    expect(await screen.findByRole('heading', { name: 'Ich' })).toBeInTheDocument();
    expect(screen.getByText('A parasitic infection commonly seen as white spots.'))
      .toBeInTheDocument();
    expect(screen.getByText('Malachite Green')).toBeInTheDocument();
    expect(screen.getByText('Quarantine new fish Maintain water quality')).toBeInTheDocument();
  });

  it('creates a treatment plan', async () => {
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Treatments' }));

    fireEvent.change(screen.getByRole('textbox', { name: 'Medicine' }), {
      target: { value: 'Malachite Green' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Dosage' }), {
      target: { value: '0.1 mg/L' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Cost' }), {
      target: { value: '500' },
    });
    fireEvent.change(screen.getByLabelText('Start Date'), {
      target: { value: '2026-08-14' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save Treatment' }));

    await waitFor(() => expect(createTreatmentPlan).toHaveBeenCalledWith(
      expect.objectContaining({
        pond: 1,
        medicine_name: 'Malachite Green',
        dosage: '0.1 mg/L',
        cost: 500,
        status: 'Planned',
      }),
    ));
  });

  it('marks all health alerts as read', async () => {
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Alerts' }));

    expect(await screen.findByText('High severity fish health case detected'))
      .toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Mark all read' }));

    await waitFor(() => expect(markFishHealthAlertsRead).toHaveBeenCalledWith('all'));
  });

  it('shows an error when diagnosis cannot be saved', async () => {
    createHealthRecord.mockRejectedValueOnce(new Error('Health record could not be saved'));
    renderWithProviders(<FishHealthManagement />);
    await screen.findByRole('heading', { name: 'Fish Health Management' });
    fireEvent.click(screen.getByRole('button', { name: 'Diagnosis Form' }));
    fireEvent.change(screen.getByRole('combobox', { name: 'Fish Stock' }), { target: { value: '101' } });
    fireEvent.click(screen.getByRole('checkbox', { name: 'white spots' }));
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Affected Count' }), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save and Diagnose' }));

    expect(await screen.findByText('Health record could not be saved')).toBeInTheDocument();
  });
});
