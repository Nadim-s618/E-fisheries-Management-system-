import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import MarketBridge from './MarketBridge';
import {
  acceptMarketOrder,
  completeMarketOrder,
  createMarketListing,
  deliverMarketOrder,
  getMarketListings,
  getMarketOrders,
  getMarketPriceRecommendation,
  getMarketProfile,
  getPondStocks,
  getPonds,
  rejectMarketOrder,
  shipMarketOrder,
  updateMarketListing,
} from '../../test/mocks/marketBridgeApi';
import {
  marketBridgePonds,
  marketBridgeStocks,
  marketListings,
  marketOrders,
  marketProfile,
} from '../../test/mocks/marketBridgeData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/marketBridgeApi'));
vi.mock('../../context/useAuth', () => ({
  useAuth: () => ({ user: { id: 7 } }),
}));

describe('MarketBridge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getMarketProfile.mockResolvedValue(marketProfile);
    getMarketListings.mockResolvedValue(marketListings);
    getMarketOrders.mockResolvedValue(marketOrders);
    getPonds.mockResolvedValue(marketBridgePonds);
    getPondStocks.mockResolvedValue(marketBridgeStocks);
    getMarketPriceRecommendation.mockResolvedValue({
      suggested_price: 255,
      low_price: 240,
      high_price: 270,
    });
    createMarketListing.mockResolvedValue({});
    updateMarketListing.mockResolvedValue({});
    acceptMarketOrder.mockResolvedValue({});
    rejectMarketOrder.mockResolvedValue({});
    shipMarketOrder.mockResolvedValue({});
    deliverMarketOrder.mockResolvedValue({});
    completeMarketOrder.mockResolvedValue({});
  });

  it('loads seller summary and current listings', async () => {
    renderWithProviders(<MarketBridge />);

    expect(await screen.findByRole('heading', { name: 'Fish Store' })).toBeInTheDocument();
    expect(screen.getByText('Active Listings')).toBeInTheDocument();
    expect(screen.getByText('75 kg')).toBeInTheDocument();
    expect(screen.getByText('Pending Orders')).toBeInTheDocument();
    expect(screen.getByText('Fresh Tilapia from North Pond')).toBeInTheDocument();
    expect(screen.getAllByText(/BDT 260/).length).toBeGreaterThan(0);
  });

  it('gets a suggested price for a manual listing', async () => {
    renderWithProviders(<MarketBridge />);
    await screen.findByRole('heading', { name: 'Fish Store' });

    fireEvent.change(screen.getByRole('textbox', { name: 'Species' }), {
      target: { value: 'Tilapia' },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'Location' }), {
      target: { value: 'Dhaka' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Quantity kg' }), {
      target: { value: '20' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Suggest price' }));

    await waitFor(() => expect(getMarketPriceRecommendation).toHaveBeenCalledWith({
      species: 'Tilapia',
      location: 'Dhaka',
      quantity_kg: '20',
      fish_stock: undefined,
    }));
    expect(await screen.findByText('Suggested range: BDT 240 to BDT 270 per kg.'))
      .toBeInTheDocument();
    expect(screen.getByDisplayValue('BDT 255')).toBeInTheDocument();
  });

  it('creates a listing using the entered form values', async () => {
    renderWithProviders(<MarketBridge />);
    await screen.findByRole('heading', { name: 'Fish Store' });

    const values = {
      Species: 'Tilapia',
      Title: 'New Tilapia Listing',
      'Quantity kg': '25',
      'Price per kg': '255',
      Location: 'Dhaka',
      'Average height (cm)': '18',
      'Average weight (g)': '350',
    };
    Object.entries(values).forEach(([label, value]) => {
      const role = ['Quantity kg', 'Price per kg', 'Average height (cm)', 'Average weight (g)'].includes(label)
        ? 'spinbutton'
        : 'textbox';
      fireEvent.change(screen.getByRole(role, { name: label }), { target: { value } });
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create listing' }));

    await waitFor(() => expect(createMarketListing).toHaveBeenCalledTimes(1));
    const payload = createMarketListing.mock.calls[0][0];
    expect(payload).toBeInstanceOf(FormData);
    expect(payload.get('species')).toBe('Tilapia');
    expect(payload.get('title')).toBe('New Tilapia Listing');
    expect(payload.get('quantity_kg')).toBe('25');
    expect(await screen.findByText('Listing created.')).toBeInTheDocument();
  });

  it('shows seller orders, buyer details, and accepts a pending order', async () => {
    renderWithProviders(<MarketBridge />);
    await screen.findByRole('heading', { name: 'Fish Store' });
    fireEvent.click(screen.getByRole('button', { name: 'Orders' }));

    expect(screen.getByText(/buyer@example.com/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accept' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'View buyer details' }));
    expect(screen.getByText('01700000000')).toBeInTheDocument();
    expect(screen.getByText('Please call before delivery.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));
    await waitFor(() => expect(acceptMarketOrder).toHaveBeenCalledWith(301));
    expect(await screen.findByText('Order updated.')).toBeInTheDocument();
  });

  it('edits and closes an active listing', async () => {
    renderWithProviders(<MarketBridge />);
    await screen.findByRole('heading', { name: 'Fish Store' });
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => expect(updateMarketListing).toHaveBeenCalledWith(201, expect.objectContaining({
      quantity_kg: 100,
      available_quantity_kg: 75,
      unit_price: 260,
    })));
  });

  it('shows an error when market data cannot be loaded', async () => {
    getMarketProfile.mockRejectedValueOnce(new Error('Market service unavailable'));
    renderWithProviders(<MarketBridge />);

    expect(await screen.findByText('Market service unavailable')).toBeInTheDocument();
  });
});
