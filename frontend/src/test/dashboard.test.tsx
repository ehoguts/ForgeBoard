import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api';
import { Dashboard } from '../pages/Dashboard';

afterEach(() => vi.restoreAllMocks());

function renderDashboard() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('dashboard states', () => {
  it('shows loading while summaries and projects are pending', () => {
    vi.spyOn(api, 'summary').mockReturnValue(new Promise(() => {}));
    vi.spyOn(api, 'projects').mockReturnValue(new Promise(() => {}));
    renderDashboard();
    expect(screen.getAllByRole('status')).toHaveLength(2);
  });

  it('shows account counts and an actionable empty project state', async () => {
    vi.spyOn(api, 'summary').mockResolvedValue({
      project_count: 0,
      total_issues: 0,
      todo: 0,
      in_progress: 0,
      done: 0,
    });
    vi.spyOn(api, 'projects').mockResolvedValue({ items: [], total: 0, offset: 0, limit: 12 });
    renderDashboard();
    expect(await screen.findByText('Your next idea belongs here.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '+ New project' })).toHaveAttribute(
      'href',
      '/projects?new=1',
    );
    expect(screen.getByText('Every next step, in one place')).toBeInTheDocument();
  });

  it('shows failures with retry controls', async () => {
    vi.spyOn(api, 'summary').mockRejectedValue(new Error('Database unavailable'));
    vi.spyOn(api, 'projects').mockRejectedValue(new Error('Projects unavailable'));
    renderDashboard();
    expect(await screen.findAllByRole('alert')).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: 'Try again' })).toHaveLength(2);
  });
});
