import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import DashboardPage from './DashboardPage';
import {
  getNotifications,
  getPondStocks,
  getPonds,
  getWaterQualityReadings,
} from '../test/mocks/pageApi';
import { pageNotifications, pagePonds } from '../test/mocks/pageData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/pageApi'));
vi.mock('../context/useAuth', () => ({
  useAuth: () => ({
    user: { first_name: 'Amina', email: 'amina@example.com' },
    logout: vi.fn(),
  }),
}));
vi.mock('../components/dashboard/DashboardTopbar', () => ({
  DashboardTopbar: ({ onHomeClick, onPondsClick }) => (
    <header>
      <button type="button" onClick={onHomeClick}>Home</button>
      <button type="button" onClick={onPondsClick}>Ponds</button>
    </header>
  ),
}));
vi.mock('../components/dashboard/DashboardSidebar', () => ({
  DashboardSidebar: ({ navItems, onNavChange }) => (
    <nav aria-label="Dashboard navigation">
      {navItems.map(item => <button type="button" key={item.id} onClick={() => onNavChange(item.id)}>{item.label}</button>)}
    </nav>
  ),
}));
vi.mock('../components/dashboard/DashboardSummary', () => ({
  DashboardSummary: ({ stats }) => <section aria-label="Dashboard summary">{stats.map(stat => <span key={stat.label}>{stat.label}: {stat.value}</span>)}</section>,
}));
vi.mock('../components/dashboard/PondManagement', () => ({ PondManagement: ({ openOnMount }) => <div>{`Pond management${openOnMount ? ' form open' : ''}`}</div> }));
vi.mock('../components/dashboard/StockGrowthManagement', () => ({ StockGrowthManagement: () => <div>Stock growth management</div> }));
vi.mock('../components/fish_health/FishHealthManagement', () => ({ default: () => <div>Fish health management</div> }));
vi.mock('../components/financials/FinancialManagement', () => ({ default: () => <div>Financial management</div> }));
vi.mock('../components/market_analysis/MarketAnalysis', () => ({ default: () => <div>Market analysis</div> }));
vi.mock('../components/market_bridge/MarketBridge', () => ({ default: () => <div>Market bridge</div> }));
vi.mock('../components/feeding/FeedingManagement', () => ({ default: () => <div>Feeding management</div> }));
vi.mock('../components/weather/WeatherManagement', () => ({ default: () => <div>Weather management</div> }));
vi.mock('../components/water_quality/WaterQualityManagement', () => ({ default: ({ initialTab }) => <div>Water quality management: {initialTab}</div> }));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getNotifications.mockResolvedValue(pageNotifications);
    getPonds.mockResolvedValue(pagePonds);
    getPondStocks.mockResolvedValue([{ current_quantity: 1200 }]);
    getWaterQualityReadings.mockResolvedValue([{ temperature: 28, dissolved_oxygen: 6 }]);
  });

  it('loads dashboard statistics and navigation content', async () => {
    renderWithProviders(<MemoryRouter><DashboardPage /></MemoryRouter>);

    await screen.findByText('Water quality management: Dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Home' }));
    expect(await screen.findByText('Total Ponds: 2')).toBeInTheDocument();
    expect(screen.getByText('Total Fish: 2,400')).toBeInTheDocument();
    expect(screen.getByText('Avg Temperature: 28.0°C')).toBeInTheDocument();
    expect(screen.getByText('Avg Oxygen: 6.0 mg/L')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Welcome to E-Fisheries/ })).toBeInTheDocument();
  });

  it('switches sections and opens the add-water-test view', async () => {
    renderWithProviders(<MemoryRouter><DashboardPage /></MemoryRouter>);
    await screen.findByText('Water quality management: Dashboard');

    fireEvent.click(screen.getByRole('button', { name: 'Weather' }));
    expect(screen.getByText('Weather management')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Home' }));
    expect(screen.getByRole('heading', { name: /Welcome to E-Fisheries/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Add water test' }));
    expect(screen.getByText('Water quality management: Add Reading')).toBeInTheDocument();
  });

  it('opens pond management from the top navigation', async () => {
    renderWithProviders(<MemoryRouter><DashboardPage /></MemoryRouter>);
    await screen.findByText('Water quality management: Dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Ponds' }));

    expect(await screen.findByText('Pond management')).toBeInTheDocument();
    await waitFor(() => expect(getPonds).toHaveBeenCalled());
  });

  it('falls back to unavailable-data labels when dashboard stats fail', async () => {
    getPondStocks.mockRejectedValueOnce(new Error('Dashboard data unavailable'));
    renderWithProviders(<MemoryRouter><DashboardPage /></MemoryRouter>);
    await screen.findByText('Water quality management: Dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Home' }));

    await waitFor(() => expect(getPonds).toHaveBeenCalled());
    expect(screen.getByText('Total Ponds: —')).toBeInTheDocument();
    expect(screen.getByText('Total Fish: —')).toBeInTheDocument();
  });
});
