import { useState } from 'react';
import type { FormEvent } from 'react';
import type { Issue, IssueInput, IssuePriority, IssueStatus } from '../api';
import { ErrorNotice } from './Feedback';

export function IssueForm({
  issue,
  pending,
  error,
  onSave,
  onCancel,
}: {
  issue?: Issue;
  pending: boolean;
  error: Error | null;
  onSave: (input: IssueInput) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(issue?.title ?? '');
  const [description, setDescription] = useState(issue?.description ?? '');
  const [status, setStatus] = useState<IssueStatus>(issue?.status ?? 'todo');
  const [priority, setPriority] = useState<IssuePriority>(issue?.priority ?? 'medium');
  const [dueDate, setDueDate] = useState(issue?.due_date ?? '');
  function submit(event: FormEvent) {
    event.preventDefault();
    if (title.trim())
      onSave({
        title: title.trim(),
        description: description.trim() || null,
        status,
        priority,
        due_date: dueDate || null,
      });
  }
  return (
    <form className="editor" onSubmit={submit}>
      <h2>{issue ? 'Edit issue' : 'Create an issue'}</h2>
      <ErrorNotice error={error} />
      <label>
        Title
        <input
          autoFocus
          required
          maxLength={200}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="What needs to happen?"
        />
      </label>
      <label>
        Description <span className="optional">optional</span>
        <textarea
          maxLength={10000}
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add context, acceptance criteria, or next steps."
        />
      </label>
      <div className="form-grid">
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value as IssueStatus)}>
            <option value="todo">To do</option>
            <option value="in_progress">In progress</option>
            <option value="done">Done</option>
          </select>
        </label>
        <label>
          Priority
          <select value={priority} onChange={(e) => setPriority(e.target.value as IssuePriority)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
        <label>
          Due date <span className="optional">optional</span>
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
        </label>
      </div>
      <div className="form-actions">
        <button className="button" disabled={pending || !title.trim()}>
          {pending ? 'Saving…' : issue ? 'Save issue' : 'Create issue'}
        </button>
        <button type="button" className="button secondary" disabled={pending} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
