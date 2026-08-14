import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ProfilePage from './ProfilePage';
import { updateUserProfile } from '../test/mocks/pageApi';
import { renderWithProviders } from '../test/utils/testUtils';

const updateUser = vi.fn();
vi.mock('../lib/api', () => import('../test/mocks/pageApi'));
vi.mock('../context/useAuth', () => ({
  useAuth: () => ({
    user: { first_name: 'Amina', last_name: 'Rahman', email: 'amina@example.com', address: 'Dhaka' },
    updateUser,
  }),
}));

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    updateUserProfile.mockResolvedValue({ user: { first_name: 'Amina' } });
  });

  it('loads user details and saves profile changes as FormData', async () => {
    renderWithProviders(<MemoryRouter><ProfilePage /></MemoryRouter>);

    expect(screen.getByRole('heading', { name: 'My Profile' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('Amina Rahman')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Address'), { target: { value: 'Chattogram' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => expect(updateUserProfile).toHaveBeenCalledTimes(1));
    const payload = updateUserProfile.mock.calls[0][0];
    expect(payload).toBeInstanceOf(FormData);
    expect(payload.get('full_name')).toBe('Amina Rahman');
    expect(payload.get('address')).toBe('Chattogram');
    expect(updateUser).toHaveBeenCalled();
    expect(await screen.findByRole('status')).toHaveTextContent('Profile updated successfully.');
  });

  it('shows profile save errors', async () => {
    updateUserProfile.mockRejectedValueOnce(new Error('Profile update failed'));
    renderWithProviders(<MemoryRouter><ProfilePage /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Profile update failed');
  });
});
