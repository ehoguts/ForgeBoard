import { useState } from 'react';
import type { FormEvent } from 'react';
import type { Project } from '../api';
import { ErrorNotice } from './Feedback';

export function ProjectForm({
  project,
  pending,
  error,
  onSave,
  onCancel,
}: {
  project?: Project;
  pending: boolean;
  error: Error | null;
  onSave: (input: { name: string; description: string }) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(project?.name ?? '');
  const [description, setDescription] = useState(project?.description ?? '');
  function submit(event: FormEvent) {
    event.preventDefault();
    if (name.trim()) onSave({ name: name.trim(), description: description.trim() });
  }
  return (
    <form className="editor" onSubmit={submit}>
      <h2>{project ? 'Edit project' : 'Create a project'}</h2>
      <ErrorNotice error={error} />
      <label>
        Project name
        <input
          autoFocus
          required
          maxLength={120}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Portfolio website"
        />
      </label>
      <label>
        Description <span className="optional">optional</span>
        <textarea
          maxLength={5000}
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What are you building?"
        />
      </label>
      <div className="form-actions">
        <button className="button" disabled={pending || !name.trim()}>
          {pending ? 'Saving…' : project ? 'Save project' : 'Create project'}
        </button>
        <button type="button" className="button secondary" disabled={pending} onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
