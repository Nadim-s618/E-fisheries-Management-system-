import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import HomePage from './HomePage';
import { renderWithProviders } from '../test/utils/testUtils';

describe('HomePage', () => {
  it('renders homepage content and navigation links immediately', () => {
    renderWithProviders(<MemoryRouter><HomePage /></MemoryRouter>);

    expect(screen.getByRole('heading', { name: /smarter aquaculture/i })).toBeInTheDocument();
    expect(screen.getAllByText('Water Quality Monitoring').length).toBeGreaterThan(0);
    expect(screen.getByText('Active ponds managed')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Fish Store' }).length).toBeGreaterThan(0);
  });
});
