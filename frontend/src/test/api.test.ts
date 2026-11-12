import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, api } from '../api';

afterEach(() => vi.unstubAllGlobals());

describe('typed API client', () => {
  it('bootstraps CSRF and sends it with same-origin credentials for writes', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ csrf_token: 'approved-csrf' }), { status: 200 }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetcher);
    await api.deleteIssue('issue-1');
    expect(fetcher).toHaveBeenNthCalledWith(
      1,
      '/api/v1/auth/csrf',
      expect.objectContaining({ credentials: 'same-origin' }),
    );
    expect(fetcher).toHaveBeenNthCalledWith(
      2,
      '/api/v1/issues/issue-1',
      expect.objectContaining({
        method: 'DELETE',
        credentials: 'same-origin',
        headers: expect.objectContaining({ 'X-CSRF-Token': 'approved-csrf' }),
      }),
    );
  });

  it('preserves safe API errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 })),
    );
    await expect(api.project('missing')).rejects.toEqual(new ApiError(404, 'Not found'));
  });
});
