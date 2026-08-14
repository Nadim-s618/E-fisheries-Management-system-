import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import HomePage from './HomePage';
import { getHomepage } from '../test/mocks/pageApi';
import { homepageData } from '../test/mocks/pageData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/pageApi'));

describe('HomePage', () => {
  beforeEach(() => getHomepage.mockResolvedValue(homepageData));

  it('loads homepage content and navigation links', async () => {
    renderWithProviders(<MemoryRouter><HomePage /></MemoryRouter>);

    expect(await screen.findByRole('heading', { name: /manage smarter fisheries/i })).toBeInTheDocument();
    expect(screen.getByText('Grow better fish')).toBeInTheDocument();
    expect(screen.getByText('Ponds managed')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Fish Store' }).length).toBeGreaterThan(0);
  });

  it('shows a backend error state', async () => {
    getHomepage.mockRejectedValueOnce(new Error('Backend unavailable'));
    renderWithProviders(<MemoryRouter><HomePage /></MemoryRouter>);

    expect(await screen.findByRole('alert')).toHaveTextContent('Homepage content is unavailable right now.');
  });
});
