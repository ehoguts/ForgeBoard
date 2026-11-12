import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { ApiError, api } from '../api';

afterEach(() => vi.restoreAllMocks());

const user = { id: 'user-1', email: 'maker@example.com', created_at: '2026-01-01' };

function renderApp() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return client;
}

function stubDashboard() {
  vi.spyOn(api, 'summary').mockResolvedValue({
    project_count: 0,
    total_issues: 0,
    todo: 0,
    in_progress: 0,
    done: 0,
  });
  vi.spyOn(api, 'projects').mockResolvedValue({ items: [], total: 0, offset: 0, limit: 12 });
}

describe('account transitions', () => {
  it('updates the mounted App after login and logout, preserving the account observer', async () => {
    vi.spyOn(api, 'me').mockRejectedValue(new ApiError(401, 'Authentication required'));
    vi.spyOn(api, 'login').mockResolvedValue(user);
    const logout = vi.spyOn(api, 'logout').mockResolvedValue(undefined);
    stubDashboard();
    const client = renderApp();
    await screen.findByRole('heading', { name: 'Welcome back.' });
    await userEvent.type(screen.getByLabelText('Email'), user.email);
    await userEvent.type(screen.getByLabelText('Password'), 'a unique passphrase');
    await userEvent.click(screen.getByRole('button', { name: 'Sign in →' }));
    expect(
      await screen.findByRole('heading', { name: 'Make room for progress.' }),
    ).toBeInTheDocument();
    expect(client.getQueryData(['me'])).toEqual(user);
    client.setQueryData(['private-account-data'], 'must disappear at logout');
    await userEvent.click(screen.getByRole('button', { name: 'Sign out ↗' }));
    expect(await screen.findByRole('heading', { name: 'Welcome back.' })).toBeInTheDocument();
    expect(logout).toHaveBeenCalledOnce();
    expect(client.getQueryData(['private-account-data'])).toBeUndefined();
    expect(client.getQueryData(['me'])).toBeNull();
  });

  it('returns an expired session to login and discards private cached data', async () => {
    vi.spyOn(api, 'me').mockResolvedValue(user);
    stubDashboard();
    const client = renderApp();
    await screen.findByRole('heading', { name: 'Make room for progress.' });
    client.setQueryData(['private-account-data'], 'must disappear at expiry');
    act(() => window.dispatchEvent(new Event('forgeboard:session-expired')));
    expect(await screen.findByRole('heading', { name: 'Welcome back.' })).toBeInTheDocument();
    await waitFor(() => expect(client.getQueryData(['private-account-data'])).toBeUndefined());
  });
});
