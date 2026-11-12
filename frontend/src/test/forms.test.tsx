import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ProjectForm } from '../components/ProjectForm';
import { IssueForm } from '../components/IssueForm';
import { IssueFilters } from '../components/IssueFilters';

describe('critical forms', () => {
  it('requires a project name, trims values, and submits the project', async () => {
    const onSave = vi.fn();
    render(<ProjectForm pending={false} error={null} onSave={onSave} onCancel={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Create project' })).toBeDisabled();
    await userEvent.type(screen.getByLabelText('Project name'), '  Portfolio  ');
    await userEvent.type(screen.getByLabelText(/Description/), '  Ship a website  ');
    await userEvent.click(screen.getByRole('button', { name: 'Create project' }));
    expect(onSave).toHaveBeenCalledWith({ name: 'Portfolio', description: 'Ship a website' });
  });

  it('submits issue fields and prevents a second submission while saving', async () => {
    const onSave = vi.fn();
    const { rerender } = render(
      <IssueForm pending={false} error={null} onSave={onSave} onCancel={vi.fn()} />,
    );
    await userEvent.type(screen.getByLabelText('Title'), 'Implement login');
    await userEvent.selectOptions(screen.getByLabelText('Status'), 'in_progress');
    await userEvent.selectOptions(screen.getByLabelText('Priority'), 'high');
    await userEvent.click(screen.getByRole('button', { name: 'Create issue' }));
    expect(onSave).toHaveBeenCalledWith({
      title: 'Implement login',
      description: null,
      status: 'in_progress',
      priority: 'high',
      due_date: null,
    });
    rerender(<IssueForm pending error={null} onSave={onSave} onCancel={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Saving…' })).toBeDisabled();
  });

  it('renders mutation errors accessibly', () => {
    render(
      <ProjectForm
        pending={false}
        error={new Error('Project name is too long')}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Project name is too long');
  });
});

describe('issue filters', () => {
  it('restores URL filters and emits status, priority, and search changes', async () => {
    const onChange = vi.fn();
    render(
      <IssueFilters
        params={new URLSearchParams('status=todo&priority=high&search=login')}
        onChange={onChange}
      />,
    );
    expect(screen.getByLabelText('Search issues')).toHaveValue('login');
    expect(screen.getByLabelText('Status')).toHaveValue('todo');
    expect(screen.getByLabelText('Priority')).toHaveValue('high');
    await userEvent.selectOptions(screen.getByLabelText('Status'), 'done');
    await userEvent.selectOptions(screen.getByLabelText('Priority'), 'low');
    expect(onChange).toHaveBeenCalledWith('status', 'done');
    expect(onChange).toHaveBeenCalledWith('priority', 'low');
    await userEvent.type(screen.getByLabelText('Search issues'), 'x');
    expect(onChange).toHaveBeenCalledWith('search', 'loginx');
  });
});
