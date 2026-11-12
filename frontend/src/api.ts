export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type IssueStatus = 'todo' | 'in_progress' | 'done';
export type IssuePriority = 'low' | 'medium' | 'high';
export interface Issue {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: IssueStatus;
  priority: IssuePriority;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface Summary {
  project_count: number;
  total_issues: number;
  todo: number;
  in_progress: number;
  done: number;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function errorMessage(body: unknown): string {
  if (typeof body !== 'object' || body === null || !('detail' in body)) {
    return 'The request could not be completed. Please try again.';
  }
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((error: unknown) => {
        if (typeof error !== 'object' || error === null || !('msg' in error)) return '';
        const field = 'loc' in error && Array.isArray(error.loc) ? error.loc.at(-1) : 'Input';
        return `${String(field)}: ${String(error.msg)}`;
      })
      .filter(Boolean)
      .join('. ');
  }
  return 'The request could not be completed. Please try again.';
}

export async function request<T>(
  path: string,
  options: { method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'; body?: unknown; csrf?: boolean } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (options.csrf) {
    const token = await request<{ csrf_token: string }>('/auth/csrf');
    headers['X-CSRF-Token'] = token.csrf_token;
  }
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method: options.method ?? 'GET',
      headers,
      credentials: 'same-origin',
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError(0, 'Cannot reach ForgeBoard. Check your connection and try again.');
  }
  if (!response.ok) {
    if (response.status === 401 && !['/auth/login', '/auth/register'].includes(path)) {
      window.dispatchEvent(new Event('forgeboard:session-expired'));
    }
    const body: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, errorMessage(body));
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  me: () => request<User>('/auth/me'),
  register: (body: { email: string; password: string }) =>
    request<User>('/auth/register', { method: 'POST', body }),
  login: (body: { email: string; password: string }) =>
    request<User>('/auth/login', { method: 'POST', body }),
  logout: () => request<void>('/auth/logout', { method: 'POST', csrf: true }),
  summary: () => request<Summary>('/dashboard/summary'),
  projects: (offset = 0) => request<Page<Project>>(`/projects?limit=12&offset=${offset}`),
  project: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (body: { name: string; description: string }) =>
    request<Project>('/projects', { method: 'POST', body, csrf: true }),
  updateProject: (id: string, body: { name: string; description: string }) =>
    request<Project>(`/projects/${id}`, { method: 'PATCH', body, csrf: true }),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE', csrf: true }),
  issues: (projectId: string, params: URLSearchParams) =>
    request<Page<Issue>>(`/projects/${projectId}/issues?${params}`),
  createIssue: (projectId: string, body: IssueInput) =>
    request<Issue>(`/projects/${projectId}/issues`, { method: 'POST', body, csrf: true }),
  updateIssue: (id: string, body: Partial<IssueInput>) =>
    request<Issue>(`/issues/${id}`, { method: 'PATCH', body, csrf: true }),
  deleteIssue: (id: string) => request<void>(`/issues/${id}`, { method: 'DELETE', csrf: true }),
};

export type IssueInput = Pick<Issue, 'title' | 'description' | 'status' | 'priority' | 'due_date'>;
