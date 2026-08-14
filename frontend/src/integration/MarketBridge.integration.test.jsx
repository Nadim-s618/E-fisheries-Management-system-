import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import MarketBridge from '../components/market_bridge/MarketBridge';
import { acceptMarketOrder, getMarketListings, getMarketOrders, getMarketProfile, getPondStocks, getPonds } from '../test/mocks/marketBridgeApi';
import { marketBridgePonds, marketBridgeStocks, marketListings, marketOrders, marketProfile } from '../test/mocks/marketBridgeData';
import { renderWithProviders } from '../test/utils/testUtils';

vi.mock('../lib/api', () => import('../test/mocks/marketBridgeApi'));
vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { id: 7 } }) }));

describe('market bridge integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getMarketProfile.mockResolvedValue(marketProfile);
    getMarketListings.mockResolvedValue(marketListings);
    getMarketOrders.mockResolvedValue(marketOrders);
    getPonds.mockResolvedValue(marketBridgePonds);
    getPondStocks.mockResolvedValue(marketBridgeStocks);
    acceptMarketOrder.mockResolvedValue({});
  });

  it('moves from listings to orders and accepts a pending order', async () => {
    renderWithProviders(<MarketBridge />);
    await screen.findByRole('heading', { name: 'Fish Store' });
    fireEvent.click(screen.getByRole('button', { name: 'Orders' }));
    expect(await screen.findByText(/buyer@example.com/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));
    await waitFor(() => expect(acceptMarketOrder).toHaveBeenCalledWith(301));
    expect(await screen.findByText('Order updated.')).toBeInTheDocument();
  });

  it('shows the market error when the seller profile cannot load', async () => {
    getMarketProfile.mockRejectedValueOnce(new Error('Market service unavailable'));
    renderWithProviders(<MarketBridge />);
    expect(await screen.findByText('Market service unavailable')).toBeInTheDocument();
  });
});
