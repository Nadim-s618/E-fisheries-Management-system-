import React from 'react';
import { fireEvent, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import HomePage from '../pages/HomePage';
import { getHomepage } from '../test/mocks/pageApi';
import { homepageData } from '../test/mocks/pageData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/pageApi'));

describe('homepage integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getHomepage.mockResolvedValue(homepageData);
  });

  it('loads homepage content and links visitors to the fish store', async () => {
    renderWithProviders(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: /manage smarter fisheries/i })).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole('link', { name: 'Fish Store' })[0]);
    expect(screen.getAllByRole('link', { name: 'Fish Store' })[0]).toHaveAttribute('href', '/fish-store');
  });

  it('shows a recoverable error when homepage content cannot load', async () => {
    getHomepage.mockRejectedValueOnce(new Error('Backend unavailable'));
    renderWithProviders(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Homepage content is unavailable right now.');
  });
});
