import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ProfilePage from '../pages/ProfilePage';
import { updateUserProfile } from '../test/mocks/pageApi';
import { renderWithProviders } from '../test/utils/testUtils';

const updateUser = vi.fn();
vi.mock('../lib/api', () => import('../test/mocks/pageApi'));
vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { first_name: 'Amina', last_name: 'Rahman', email: 'amina@example.com', address: 'Dhaka' }, updateUser }) }));

describe('profile integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    updateUserProfile.mockResolvedValue({ user: { first_name: 'Amina' } });
  });

  it('edits profile details, saves them, and updates the authenticated user', async () => {
    renderWithProviders(<MemoryRouter><ProfilePage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Address'), { target: { value: 'Chattogram' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
    await waitFor(() => expect(updateUserProfile).toHaveBeenCalledTimes(1));
    expect(updateUser).toHaveBeenCalledWith({ first_name: 'Amina' });
    expect(await screen.findByRole('status')).toHaveTextContent('Profile updated successfully.');
  });

  it('shows an error when profile saving fails', async () => {
    updateUserProfile.mockRejectedValueOnce(new Error('Profile update failed'));
    renderWithProviders(<MemoryRouter><ProfilePage /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Profile update failed');
  });
});
