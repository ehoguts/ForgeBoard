import { useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import type { Issue, IssueInput } from '../api';
import { Empty, ErrorNotice, Loading, Pagination } from '../components/Feedback';
import { ProjectForm } from '../components/ProjectForm';
import { IssueForm } from '../components/IssueForm';
import { IssueFilters } from '../components/IssueFilters';

const statusLabels = { todo: 'To do', in_progress: 'In progress', done: 'Done' };

export function ProjectDetail() {
  const { projectId = '' } = useParams();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [editProject, setEditProject] = useState(false);
  const [issueEditor, setIssueEditor] = useState<Issue | 'new' | null>(null);
  const [message, setMessage] = useState('');
  const client = useQueryClient();
  const offset = Math.max(0, Number(params.get('offset')) || 0);
  const filters = new URLSearchParams({ limit: '10', offset: String(offset) });
  for (const field of ['status', 'priority', 'search']) {
    const value = params.get(field);
    if (value) filters.set(field, value);
  }
  const project = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.project(projectId),
  });
  const issues = useQuery({
    queryKey: ['issues', projectId, filters.toString()],
    queryFn: () => api.issues(projectId, filters),
    enabled: project.isSuccess,
  });
  function invalidate() {
    void client.invalidateQueries({ queryKey: ['issues', projectId] });
    void client.invalidateQueries({ queryKey: ['summary'] });
    void client.invalidateQueries({ queryKey: ['projects'] });
  }
  const updateProject = useMutation({
    mutationFn: (input: { name: string; description: string }) =>
      api.updateProject(projectId, input),
    onSuccess: (updated) => {
      client.setQueryData(['project', projectId], updated);
      invalidate();
      setEditProject(false);
      setMessage('Project updated.');
    },
  });
  const deleteProject = useMutation({
    mutationFn: () => api.deleteProject(projectId),
    onSuccess: () => {
      invalidate();
      navigate('/projects');
    },
  });
  const saveIssue = useMutation({
    mutationFn: (input: IssueInput) =>
      issueEditor && issueEditor !== 'new'
        ? api.updateIssue(issueEditor.id, input)
        : api.createIssue(projectId, input),
    onSuccess: () => {
      invalidate();
      setIssueEditor(null);
      setMessage('Issue saved.');
    },
  });
  const deleteIssue = useMutation({
    mutationFn: api.deleteIssue,
    onSuccess: () => {
      invalidate();
      setMessage('Issue deleted.');
    },
  });
  const changeStatus = useMutation({
    mutationFn: ({ id, status }: Pick<Issue, 'id' | 'status'>) => api.updateIssue(id, { status }),
    onSuccess: () => {
      invalidate();
      setMessage('Status updated.');
    },
  });
  function updateFilter(field: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(field, value);
    else next.delete(field);
    next.delete('offset');
    setParams(next, { replace: true });
  }
  if (project.isPending) return <Loading />;
  if (project.isError)
    return (
      <>
        <Link to="/projects" className="back-link">
          ← All projects
        </Link>
        <ErrorNotice error={project.error} retry={() => void project.refetch()} />
      </>
    );
  return (
    <>
      <Link to="/projects" className="back-link">
        ← All projects
      </Link>
      <header className="page-heading">
        <div>
          <span className="eyebrow">PROJECT WORKSPACE</span>
          <h1>{project.data.name}</h1>
          <p className="project-description">
            {project.data.description || 'One issue at a time. Let’s build something.'}
          </p>
        </div>
        <div className="heading-actions">
          <button
            className="button secondary"
            onClick={() => {
              updateProject.reset();
              setEditProject(!editProject);
            }}
          >
            Edit project
          </button>
          <button
            className="button"
            onClick={() => {
              saveIssue.reset();
              setIssueEditor('new');
            }}
          >
            + New issue
          </button>
        </div>
      </header>
      {message && (
        <p className="notice success" role="status">
          {message}
        </p>
      )}
      <ErrorNotice error={deleteProject.error ?? deleteIssue.error ?? changeStatus.error} />
      {editProject && (
        <>
          <ProjectForm
            project={project.data}
            pending={updateProject.isPending}
            error={updateProject.error}
            onSave={(input) => updateProject.mutate(input)}
            onCancel={() => setEditProject(false)}
          />
          <div className="danger-zone">
            <span>Delete this project and all its issues.</span>
            <button
              className="text-button danger"
              disabled={deleteProject.isPending}
              onClick={() => {
                if (
                  window.confirm(
                    `Delete “${project.data.name}” and all its issues? This cannot be undone.`,
                  )
                )
                  deleteProject.mutate();
              }}
            >
              Delete project
            </button>
          </div>
        </>
      )}
      {issueEditor && (
        <IssueForm
          key={issueEditor === 'new' ? 'new' : issueEditor.id}
          issue={issueEditor === 'new' ? undefined : issueEditor}
          pending={saveIssue.isPending}
          error={saveIssue.error}
          onSave={(input) => saveIssue.mutate(input)}
          onCancel={() => setIssueEditor(null)}
        />
      )}
      <section className="panel issue-panel">
        <div className="section-heading">
          <h2>
            Issues <span className="count">{issues.data?.total ?? '—'}</span>
          </h2>
          <span className="muted small-text">Newest first</span>
        </div>
        <IssueFilters params={params} onChange={updateFilter} />
        {issues.isPending ? (
          <Loading>Loading issues…</Loading>
        ) : issues.isError ? (
          <ErrorNotice error={issues.error} retry={() => void issues.refetch()} />
        ) : (
          <>
            {issues.data.items.length ? (
              <ul className="issue-list">
                {issues.data.items.map((issue) => (
                  <li className="issue-row" key={issue.id}>
                    <div className="issue-content">
                      <div className="issue-title">
                        <i className={`dot ${issue.status}`} />
                        <button
                          className="issue-name"
                          onClick={() => {
                            saveIssue.reset();
                            setIssueEditor(issue);
                          }}
                        >
                          {issue.title}
                        </button>
                      </div>
                      {issue.description && <p>{issue.description}</p>}
                      <div className="issue-meta">
                        <span className={`priority ${issue.priority}`}>{issue.priority}</span>
                        {issue.due_date && <span>Due {issue.due_date}</span>}
                        <span>
                          Created{' '}
                          {new Date(issue.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                    </div>
                    <div className="issue-actions">
                      <label className="sr-only" htmlFor={`status-${issue.id}`}>
                        Status for {issue.title}
                      </label>
                      <select
                        id={`status-${issue.id}`}
                        className={`status-select ${issue.status}`}
                        value={issue.status}
                        disabled={changeStatus.isPending}
                        onChange={(event) =>
                          changeStatus.mutate({
                            id: issue.id,
                            status: event.target.value as Issue['status'],
                          })
                        }
                      >
                        {Object.entries(statusLabels).map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                      <button
                        className="text-button"
                        onClick={() => {
                          saveIssue.reset();
                          setIssueEditor(issue);
                        }}
                      >
                        Edit<span className="sr-only"> {issue.title}</span>
                      </button>
                      <button
                        className="text-button danger"
                        disabled={deleteIssue.isPending}
                        onClick={() => {
                          if (window.confirm(`Delete issue “${issue.title}”?`))
                            deleteIssue.mutate(issue.id);
                        }}
                      >
                        Delete<span className="sr-only"> {issue.title}</span>
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty
                title={
                  filters.has('status') || filters.has('priority') || filters.has('search')
                    ? 'No issues match these filters.'
                    : 'A clear board. A fresh start.'
                }
              >
                {filters.has('status') || filters.has('priority') || filters.has('search')
                  ? 'Try another search or adjust the status and priority filters.'
                  : 'Create an issue to turn your next step into something actionable.'}
              </Empty>
            )}
            <Pagination
              offset={offset}
              limit={10}
              total={issues.data.total}
              onChange={(nextOffset) => {
                const next = new URLSearchParams(params);
                next.set('offset', String(nextOffset));
                setParams(next);
              }}
            />
          </>
        )}
      </section>
    </>
  );
}
