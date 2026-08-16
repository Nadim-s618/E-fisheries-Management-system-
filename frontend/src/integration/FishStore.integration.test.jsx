import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FishStorePage from '../pages/FishStorePage';
import { createPublicMashrafeeCartOrder, getPublicMashrafeeStore, trackPublicMashrafeeOrder } from '../test/mocks/pageApi';
import { fishStoreListings, placedOrder } from '../test/mocks/pageData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/pageApi'));
vi.mock('../context/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: false }),
}));

describe('fish store integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPublicMashrafeeStore.mockResolvedValue(fishStoreListings);
    createPublicMashrafeeCartOrder.mockResolvedValue(placedOrder);
    trackPublicMashrafeeOrder.mockResolvedValue({ transaction_code: 'MF-ABC123', orders: placedOrder });
  });

  it('adds fish to the cart, places an order, and displays the receipt', async () => {
    renderWithProviders(<MemoryRouter><FishStorePage /></MemoryRouter>);
    await screen.findByText('Fresh Tilapia from North Pond');
    fireEvent.click(screen.getByRole('button', { name: 'Place order' }));
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Test Buyer' } });
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '01700000000' } });
    fireEvent.change(screen.getByLabelText('Delivery address'), { target: { value: 'Dhaka' } });
    fireEvent.click(screen.getByRole('button', { name: 'Order all items' }));
    await waitFor(() => expect(createPublicMashrafeeCartOrder).toHaveBeenCalled());
    expect((await screen.findAllByText(/MF-ABC123/)).length).toBeGreaterThan(0);
  });

  it('shows an unavailable state when the store request fails', async () => {
    getPublicMashrafeeStore.mockRejectedValueOnce(new Error('Store unavailable'));
    renderWithProviders(<MemoryRouter><FishStorePage /></MemoryRouter>);
    expect(await screen.findByRole('alert')).toHaveTextContent('The fish store is unavailable right now.');
  });
});
