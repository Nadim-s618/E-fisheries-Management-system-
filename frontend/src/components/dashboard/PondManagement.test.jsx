import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { PondManagement } from './PondManagement';
import { createPond, deletePond, getPonds } from '../../test/mocks/pondApi';
import { pondRecords } from '../../test/mocks/pondData';
import { renderWithProviders } from '../../test/utils/testUtils';

vi.mock('../../lib/api', () => import('../../test/mocks/pondApi'));

describe('PondManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getPonds.mockResolvedValue(pondRecords);
    createPond.mockResolvedValue({ ...pondRecords[0], id: 2, name: 'South Pond' });
    deletePond.mockResolvedValue({});
  });

  it('loads pond summaries and creates a new pond', async () => {
    renderWithProviders(<PondManagement />);
    expect(await screen.findByRole('heading', { name: 'Pond Management' })).toBeInTheDocument();
    expect(screen.getByText('North Pond')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '+ Add pond' }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Pond name' }), { target: { value: 'South Pond' } });
    fireEvent.change(screen.getByRole('textbox', { name: 'Location' }), { target: { value: 'Khulna' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Area (decimal)' }), { target: { value: '15' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Avg depth (ft)' }), { target: { value: '4' } });
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Stocking capacity' }), { target: { value: '3000' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save pond' }));
    await waitFor(() => expect(createPond).toHaveBeenCalledWith(expect.objectContaining({ name: 'South Pond', stocking_capacity: 3000 })));
  });

  it('shows loading errors and does not delete without confirmation', async () => {
    getPonds.mockRejectedValueOnce(new Error('Pond service unavailable'));
    renderWithProviders(<PondManagement />);
    expect(await screen.findByText('Pond service unavailable')).toBeInTheDocument();
    getPonds.mockResolvedValueOnce(pondRecords);
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderWithProviders(<PondManagement />);
    await screen.findByText('North Pond');
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(deletePond).not.toHaveBeenCalled();
    window.confirm.mockRestore();
  });
});
