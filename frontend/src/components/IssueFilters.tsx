export function IssueFilters({
  params,
  onChange,
}: {
  params: URLSearchParams;
  onChange: (field: string, value: string) => void;
}) {
  return (
    <div className="filters" role="search" aria-label="Filter issues">
      <label className="search-field">
        <span>Search issues</span>
        <input
          type="search"
          maxLength={200}
          placeholder="Search by title…"
          value={params.get('search') ?? ''}
          onChange={(e) => onChange('search', e.target.value)}
        />
      </label>
      <label>
        <span>Status</span>
        <select
          value={params.get('status') ?? ''}
          onChange={(e) => onChange('status', e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="todo">To do</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
        </select>
      </label>
      <label>
        <span>Priority</span>
        <select
          value={params.get('priority') ?? ''}
          onChange={(e) => onChange('priority', e.target.value)}
        >
          <option value="">All priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
    </div>
  );
}
