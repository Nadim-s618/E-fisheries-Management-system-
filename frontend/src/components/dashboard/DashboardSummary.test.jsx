import React from 'react';
import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DashboardSummary } from './DashboardSummary';
import { renderWithProviders } from '../../test/utils/testUtils';

const stats = [
  { label: 'Total Ponds', value: '5', sub: '4 healthy', accent: 'teal' },
  { label: 'Total Fish', value: '2,000', sub: 'across all ponds', accent: 'blue' },
  { label: 'Avg Temperature', value: '21.7°C', sub: 'within range', accent: 'amber' },
  { label: 'Avg Oxygen', value: '8.1 mg/L', sub: 'optimal', accent: 'green' },
];

describe('DashboardSummary', () => {
  it('renders active alerts with pond and issue details', () => {
    renderWithProviders(
      <DashboardSummary
        alerts={[
          { pond: 'Purba Madhnagar', issue: 'High oxygen level' },
          { pond: 'Dighi', issue: 'Low pH level' },
        ]}
        stats={stats}
      />,
    );

    expect(screen.getByRole('region', { name: 'Active alerts' })).toBeInTheDocument();
    expect(screen.getByText('Purba Madhnagar')).toBeInTheDocument();
    expect(screen.getByText('High oxygen level')).toBeInTheDocument();
    expect(screen.getByText('Dighi')).toBeInTheDocument();
    expect(screen.getByText('Low pH level')).toBeInTheDocument();
  });

  it('renders every dashboard statistic', () => {
    renderWithProviders(<DashboardSummary alerts={[]} stats={stats} />);

    stats.forEach(stat => {
      expect(screen.getByText(stat.label)).toBeInTheDocument();
      expect(screen.getByText(stat.value)).toBeInTheDocument();
      expect(screen.getByText(stat.sub)).toBeInTheDocument();
    });
  });

  it('supports empty alerts without rendering an alert row', () => {
    renderWithProviders(<DashboardSummary alerts={[]} stats={stats} />);

    const alertRegion = screen.getByRole('region', { name: 'Active alerts' });
    expect(alertRegion.querySelectorAll('.dp-alert-row')).toHaveLength(0);
  });
});
