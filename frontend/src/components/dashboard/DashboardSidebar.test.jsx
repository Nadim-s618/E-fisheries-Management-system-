import React from 'react';
import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { DashboardSidebar } from './DashboardSidebar';
import { DASHBOARD_NAV_ITEMS } from '../../data/dashboard';
import { renderWithProviders } from '../../test/utils/testUtils';

function renderSidebar(overrides = {}) {
  const props = {
    activeNav: 'water',
    navItems: DASHBOARD_NAV_ITEMS,
    onAddPond: vi.fn(),
    onNavChange: vi.fn(),
    onLogout: vi.fn(),
    ...overrides,
  };

  return { ...renderWithProviders(<DashboardSidebar {...props} />), props };
}

describe('DashboardSidebar', () => {
  it('renders all dashboard navigation items', () => {
    renderSidebar();

    DASHBOARD_NAV_ITEMS.forEach(item => {
      expect(screen.getByRole('button', { name: item.label })).toBeInTheDocument();
    });
  });

  it('marks the active navigation item as the current page', () => {
    renderSidebar({ activeNav: 'finance' });

    expect(screen.getByRole('button', { name: 'Financials' }))
      .toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('button', { name: 'Weather' }))
      .not.toHaveAttribute('aria-current');
  });

  it('calls the navigation callback when a module is selected', () => {
    const onNavChange = vi.fn();
    renderSidebar({ onNavChange });

    fireEvent.click(screen.getByRole('button', { name: 'Fish Health' }));

    expect(onNavChange).toHaveBeenCalledWith('health');
  });

  it('calls the add pond callback', () => {
    const onAddPond = vi.fn();
    renderSidebar({ onAddPond });

    fireEvent.click(screen.getByRole('button', { name: 'Add New Pond' }));

    expect(onAddPond).toHaveBeenCalledTimes(1);
  });

  it('calls the logout callback when signing out', () => {
    const onLogout = vi.fn();
    renderSidebar({ onLogout });

    fireEvent.click(screen.getByRole('button', { name: 'Sign Out' }));

    expect(onLogout).toHaveBeenCalledTimes(1);
  });
});
