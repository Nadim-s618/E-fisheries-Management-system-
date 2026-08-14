import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AuthPage from './AuthPage';
import { renderWithProviders } from '../test/utils/testUtils';

const auth = { isAuthenticated: false, isLoading: false, login: vi.fn(), signup: vi.fn() };
vi.mock('../context/useAuth', () => ({ useAuth: () => auth }));

describe('AuthPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth.isAuthenticated = false;
    auth.isLoading = false;
  });

  it('submits login credentials', async () => {
    auth.login.mockResolvedValueOnce({});
    renderWithProviders(<MemoryRouter><AuthPage /></MemoryRouter>);

    fireEvent.change(screen.getByRole('textbox', { name: 'Email' }), { target: { value: 'farmer@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => expect(auth.login).toHaveBeenCalledWith({ email: 'farmer@example.com', password: 'password123' }));
  });

  it('shows signup fields and authentication errors', async () => {
    auth.signup.mockRejectedValueOnce(new Error('Email already exists'));
    renderWithProviders(<MemoryRouter><AuthPage mode="signup" /></MemoryRouter>);

    expect(screen.getByRole('heading', { name: 'Sign up' })).toBeInTheDocument();
    fireEvent.change(screen.getByRole('textbox', { name: 'Full name' }), { target: { value: 'Test Farmer' } });
    fireEvent.change(screen.getByRole('textbox', { name: 'Email' }), { target: { value: 'farmer@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Email already exists');
  });
});
