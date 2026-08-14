import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import WeatherManagement from './WeatherManagement';
import { getPonds, getWeatherDashboard } from '../../test/mocks/weatherApi';
import {
  southWeatherDashboard,
  weatherDashboard,
  weatherPonds,
} from '../../test/mocks/weatherData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/weatherApi'));

describe('WeatherManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(weatherPonds);
    getWeatherDashboard.mockResolvedValue(weatherDashboard);
  });

  it('loads and displays the selected pond weather report', async () => {
    renderWithProviders(<WeatherManagement />);

    expect(await screen.findByRole('heading', { name: 'Pond Weather Dashboard' })).toBeInTheDocument();
    expect(await screen.findByText("Today's Weather")).toBeInTheDocument();
    expect(screen.getByText('28 °C')).toBeInTheDocument();
    expect(screen.getByText('Fish Weather Risk')).toBeInTheDocument();
    expect(screen.getByText('Feed at 6 AM.')).toBeInTheDocument();
    expect(getWeatherDashboard).toHaveBeenCalledWith('1');
  });

  it('refreshes weather data for the selected pond', async () => {
    renderWithProviders(<WeatherManagement />);
    await screen.findByText("Today's Weather");

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));

    await waitFor(() => expect(getWeatherDashboard).toHaveBeenLastCalledWith('1', { refresh: true }));
  });

  it('loads weather for a different pond when the selection changes', async () => {
    getWeatherDashboard.mockResolvedValueOnce(weatherDashboard).mockResolvedValueOnce(southWeatherDashboard);
    renderWithProviders(<WeatherManagement />);
    await screen.findByText("Today's Weather");

    fireEvent.change(screen.getByRole('combobox', { name: 'Pond' }), { target: { value: '2' } });

    expect(await screen.findByText('31 °C')).toBeInTheDocument();
    expect(getWeatherDashboard).toHaveBeenLastCalledWith('2');
    expect(screen.getByText('Rajshahi, BD')).toBeInTheDocument();
  });

  it('shows an empty state when the user has no ponds', async () => {
    getPonds.mockResolvedValueOnce([]);
    renderWithProviders(<WeatherManagement />);

    expect(await screen.findByText('Add a pond before viewing weather reports.')).toBeInTheDocument();
    expect(getWeatherDashboard).not.toHaveBeenCalled();
  });

  it('shows the weather service error', async () => {
    getWeatherDashboard.mockRejectedValueOnce(new Error('Weather service unavailable'));
    renderWithProviders(<WeatherManagement />);

    expect(await screen.findByText('Weather service unavailable')).toBeInTheDocument();
  });
});
