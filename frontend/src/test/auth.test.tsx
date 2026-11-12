import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthPage } from '../pages/AuthPage';
import { api } from '../api';

function renderAuth(register = false) {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[register ? '/register' : '/login']}>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<AuthPage register />} />
          <Route path="/" element={<h1>Workspace overview</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return client;
}

describe('authentication', () => {
  it('logs in using credentials and opens the workspace', async () => {
    const login = vi
      .spyOn(api, 'login')
      .mockResolvedValue({ id: 'user-1', email: 'maker@example.com', created_at: '2026-01-01' });
    const client = renderAuth();
    await userEvent.type(screen.getByLabelText('Email'), 'maker@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'a unique passphrase');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in →' }));
    expect(await screen.findByRole('heading', { name: 'Workspace overview' })).toBeInTheDocument();
    expect(login).toHaveBeenCalledWith({
      email: 'maker@example.com',
      password: 'a unique passphrase',
    });
    expect(client.getQueryData(['me'])).toMatchObject({ email: 'maker@example.com' });
    login.mockRestore();
  });

  it('shows an API error and allows retrying', async () => {
    const login = vi.spyOn(api, 'login').mockRejectedValue(new Error('Invalid email or password'));
    renderAuth();
    await userEvent.type(screen.getByLabelText('Email'), 'maker@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'incorrect password');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in →' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password');
    await waitFor(() => expect(screen.getByRole('button', { name: 'Sign in →' })).toBeEnabled());
    login.mockRestore();
  });

  it('registers and returns to login without assuming an authenticated session', async () => {
    const register = vi
      .spyOn(api, 'register')
      .mockResolvedValue({ id: 'user-1', email: 'maker@example.com', created_at: '2026-01-01' });
    const client = renderAuth(true);
    await userEvent.type(screen.getByLabelText('Email'), 'maker@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'a unique passphrase');
    await userEvent.click(screen.getByRole('button', { name: 'Create account →' }));
    expect(await screen.findByRole('heading', { name: 'Welcome back.' })).toBeInTheDocument();
    expect(client.getQueryData(['me'])).toBeUndefined();
    register.mockRestore();
  });
});
