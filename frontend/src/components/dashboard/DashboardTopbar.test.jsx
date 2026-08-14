import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { DashboardTopbar } from './DashboardTopbar';
import { getAiAdvisor, getPonds } from '../../test/mocks/api';
import { aiAdvice, ponds } from '../../test/mocks/data';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/api'));

describe('DashboardTopbar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(ponds);
    getAiAdvisor.mockResolvedValue(aiAdvice);
  });

  it('opens notifications and marks all notifications as read', async () => {
    const onNotificationsRead = vi.fn();
    renderWithProviders(<MemoryRouter><DashboardTopbar user={{ first_name: 'Amina' }} notifications={[{ id: 1, pond_name: 'North Pond', parameter: 'pH', priority: 'High', reason: 'Low pH' }]} onNotificationsRead={onNotificationsRead} /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: /Notifications/ }));
    expect(screen.getByText('Low pH')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Mark all read' }));
    await waitFor(() => expect(onNotificationsRead).toHaveBeenCalledTimes(1));
  });

  it('loads AI pond tips and shows an API error', async () => {
    renderWithProviders(<MemoryRouter><DashboardTopbar user={{ first_name: 'Amina' }} /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Tips' }));
    expect(await screen.findByText('Improve water quality before the next feeding.')).toBeInTheDocument();
    expect(getAiAdvisor).toHaveBeenCalledWith(1);

    getAiAdvisor.mockRejectedValueOnce(new Error('Advisor unavailable'));
    fireEvent.change(screen.getByRole('combobox', { name: 'Pond' }), { target: { value: '2' } });
    expect(await screen.findByText('Advisor unavailable')).toBeInTheDocument();
  });
});
