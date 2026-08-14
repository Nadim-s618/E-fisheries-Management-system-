import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import DashboardPage from '../pages/DashboardPage';
import { getNotifications, getPondStocks, getPonds, getWaterQualityReadings } from '../test/mocks/pageApi';
import { pageNotifications, pagePonds } from '../test/mocks/pageData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/pageApi'));
vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { first_name: 'Amina' }, logout: vi.fn() }) }));
vi.mock('../components/dashboard/DashboardTopbar', () => ({ DashboardTopbar: ({ onHomeClick, onPondsClick }) => <header><button onClick={onHomeClick}>Home</button><button onClick={onPondsClick}>Ponds</button></header> }));
vi.mock('../components/dashboard/DashboardSidebar', () => ({ DashboardSidebar: ({ navItems, onNavChange }) => <nav>{navItems.map(item => <button key={item.id} onClick={() => onNavChange(item.id)}>{item.label}</button>)}</nav> }));
vi.mock('../components/dashboard/DashboardSummary', () => ({ DashboardSummary: ({ stats }) => <section aria-label="Dashboard summary">{stats.map(stat => <span key={stat.label}>{stat.label}: {stat.value}</span>)}</section> }));
vi.mock('../components/dashboard/PondManagement', () => ({ PondManagement: () => <div>Pond management</div> }));
vi.mock('../components/dashboard/StockGrowthManagement', () => ({ StockGrowthManagement: () => <div>Stock growth management</div> }));
vi.mock('../components/fish_health/FishHealthManagement', () => ({ default: () => <div>Fish health management</div> }));
vi.mock('../components/financials/FinancialManagement', () => ({ default: () => <div>Financial management</div> }));
vi.mock('../components/market_analysis/MarketAnalysis', () => ({ default: () => <div>Market analysis</div> }));
vi.mock('../components/market_bridge/MarketBridge', () => ({ default: () => <div>Market bridge</div> }));
vi.mock('../components/feeding/FeedingManagement', () => ({ default: () => <div>Feeding management</div> }));
vi.mock('../components/weather/WeatherManagement', () => ({ default: () => <div>Weather management</div> }));
vi.mock('../components/water_quality/WaterQualityManagement', () => ({ default: ({ initialTab }) => <div>Water quality management: {initialTab}</div> }));

describe('dashboard integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getNotifications.mockResolvedValue(pageNotifications);
    getPonds.mockResolvedValue(pagePonds);
    getPondStocks.mockResolvedValue([{ current_quantity: 1200 }]);
    getWaterQualityReadings.mockResolvedValue([{ temperature: 28, dissolved_oxygen: 6 }]);
  });

  it('loads aggregate statistics and navigates between dashboard sections', async () => {
    renderWithProviders(<MemoryRouter><DashboardPage /></MemoryRouter>);
    await screen.findByText('Water quality management: Dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Home' }));
    expect(await screen.findByText('Total Ponds: 2')).toBeInTheDocument();
    expect(screen.getByText('Total Fish: 2,400')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Financials' }));
    expect(screen.getByText('Financial management')).toBeInTheDocument();
  });

  it('shows unavailable labels when dashboard data fails', async () => {
    getPondStocks.mockRejectedValueOnce(new Error('Dashboard data unavailable'));
    renderWithProviders(<MemoryRouter><DashboardPage /></MemoryRouter>);
    await screen.findByText('Water quality management: Dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Home' }));
    await waitFor(() => expect(getPonds).toHaveBeenCalled());
    expect(screen.getByText('Total Ponds: —')).toBeInTheDocument();
    expect(screen.getByText('Total Fish: —')).toBeInTheDocument();
  });
});
