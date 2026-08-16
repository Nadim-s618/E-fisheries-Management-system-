import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import FishStorePage from './FishStorePage';
import {
  createPublicMashrafeeCartOrder,
  getPublicMashrafeeStore,
  trackPublicMashrafeeOrder,
} from '../test/mocks/pageApi';
import { fishStoreListings, placedOrder } from '../test/mocks/pageData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/pageApi'));
vi.mock('../context/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: false }),
}));

describe('FishStorePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPublicMashrafeeStore.mockResolvedValue(fishStoreListings);
    createPublicMashrafeeCartOrder.mockResolvedValue(placedOrder);
    trackPublicMashrafeeOrder.mockResolvedValue({ transaction_code: 'MF-ABC123', orders: placedOrder });
  });

  it('loads listings and filters fish by search', async () => {
    renderWithProviders(<MemoryRouter><FishStorePage /></MemoryRouter>);

    expect(await screen.findByRole('heading', { name: /Fish Store/ })).toBeInTheDocument();
    expect(screen.getByText('Fresh Tilapia from North Pond')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Search fish' }));
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search fish' }), { target: { value: 'Rui' } });

    expect(screen.getByText('No fish found for “Rui”.')).toBeInTheDocument();
  });

  it('adds a listing to the cart and places an order', async () => {
    renderWithProviders(<MemoryRouter><FishStorePage /></MemoryRouter>);
    await screen.findByText('Fresh Tilapia from North Pond');
    fireEvent.click(screen.getByRole('button', { name: 'Place order' }));

    expect(screen.getByRole('heading', { name: 'Fish cart' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Your name'), { target: { value: 'Test Buyer' } });
    fireEvent.change(screen.getByLabelText('Mobile number'), { target: { value: '01700000000' } });
    fireEvent.change(screen.getByLabelText('Delivery address'), { target: { value: 'Dhaka' } });
    fireEvent.click(screen.getByRole('button', { name: 'Order all items' }));

    await waitFor(() => expect(createPublicMashrafeeCartOrder).toHaveBeenCalledWith(expect.objectContaining({
      items: [{ listing: 1, quantity_kg: 1 }],
      buyer_full_name: 'Test Buyer',
    })));
    expect((await screen.findAllByText(/MF-ABC123/)).length).toBeGreaterThan(0);
  });

  it('tracks an existing transaction code', async () => {
    renderWithProviders(<MemoryRouter><FishStorePage /></MemoryRouter>);
    await screen.findByText('Track your order');
    fireEvent.change(screen.getByRole('textbox', { name: 'Transaction code' }), { target: { value: 'mf-abc123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Track' }));

    await waitFor(() => expect(trackPublicMashrafeeOrder).toHaveBeenCalledWith('MF-ABC123'));
    expect(await screen.findByText('Order placed')).toBeInTheDocument();
  });

  it('shows an error when the store cannot be loaded', async () => {
    getPublicMashrafeeStore.mockRejectedValueOnce(new Error('Store unavailable'));
    renderWithProviders(<MemoryRouter><FishStorePage /></MemoryRouter>);

    expect(await screen.findByRole('alert')).toHaveTextContent('The fish store is unavailable right now.');
  });
});
