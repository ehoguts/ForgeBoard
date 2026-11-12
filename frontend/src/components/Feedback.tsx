import type { ReactNode } from 'react';

export function ErrorNotice({ error, retry }: { error: Error | null; retry?: () => void }) {
  if (!error) return null;
  return (
    <div className="notice error" role="alert">
      <span>{error.message}</span>
      {retry && (
        <button className="text-button" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function Loading({ children = 'Loading your workspace…' }: { children?: ReactNode }) {
  return (
    <p className="loading" role="status">
      <span className="spinner" />
      {children}
    </p>
  );
}

export function Empty({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="empty">
      <span className="empty-mark" aria-hidden="true">
        ◇
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}

export function Pagination({
  offset,
  limit,
  total,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}) {
  if (total <= limit && offset === 0) return null;
  return (
    <nav className="pagination" aria-label="Pagination">
      <span>
        {total === 0 ? 0 : offset + 1}–{Math.min(offset + limit, total)} of {total}
      </span>
      <button
        className="button secondary small"
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        Previous
      </button>
      <button
        className="button secondary small"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        Next
      </button>
    </nav>
  );
}
