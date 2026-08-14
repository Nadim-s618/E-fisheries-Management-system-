import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AuthPage from '../pages/AuthPage';
import { renderWithProviders } from '../test/utils/testUtils';

const auth = { isAuthenticated: false, isLoading: false, login: vi.fn(), signup: vi.fn() };
vi.mock('../context/useAuth', () => ({ useAuth: () => auth }));

describe('authentication integration flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.isAuthenticated = false;
    auth.isLoading = false;
  });

  it('submits login details and transitions toward the dashboard', async () => {
    auth.login.mockResolvedValueOnce({});
    renderWithProviders(<MemoryRouter><AuthPage /></MemoryRouter>);

    fireEvent.change(screen.getByRole('textbox', { name: 'Email' }), { target: { value: 'farmer@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => expect(auth.login).toHaveBeenCalledWith({
      email: 'farmer@example.com',
      password: 'password123',
    }));
  });

  it('keeps the user on authentication failure and displays the error', async () => {
    auth.login.mockRejectedValueOnce(new Error('Invalid credentials'));
    renderWithProviders(<MemoryRouter><AuthPage /></MemoryRouter>);
    fireEvent.change(screen.getByRole('textbox', { name: 'Email' }), { target: { value: 'wrong@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrongpass' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
  });
});
