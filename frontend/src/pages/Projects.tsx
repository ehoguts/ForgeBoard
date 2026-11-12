import { Link, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import { Empty, ErrorNotice, Loading, Pagination } from '../components/Feedback';
import { ProjectForm } from '../components/ProjectForm';

export function Projects() {
  const [params, setParams] = useSearchParams();
  const offset = Math.max(0, Number(params.get('offset')) || 0);
  const showForm = params.has('new');
  const client = useQueryClient();
  const projects = useQuery({
    queryKey: ['projects', offset],
    queryFn: () => api.projects(offset),
  });
  const create = useMutation({
    mutationFn: api.createProject,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['projects'] });
      void client.invalidateQueries({ queryKey: ['summary'] });
      setParams({});
    },
  });
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">FROM IDEA TO SOMETHING REAL</span>
          <h1>Your projects.</h1>
          <p>A little organization for everything you’re building.</p>
        </div>
        <button
          className="button"
          onClick={() => {
            create.reset();
            setParams({ new: '1' });
          }}
        >
          + New project
        </button>
      </header>
      {showForm && (
        <ProjectForm
          pending={create.isPending}
          error={create.error}
          onSave={(input) => create.mutate(input)}
          onCancel={() => setParams({})}
        />
      )}
      {create.isSuccess && (
        <p className="notice success" role="status">
          Project created. Open it to add your first issue.
        </p>
      )}
      {projects.isPending ? (
        <Loading />
      ) : projects.isError ? (
        <ErrorNotice error={projects.error} retry={() => void projects.refetch()} />
      ) : (
        <>
          {projects.data.items.length ? (
            <div className="project-grid">
              {projects.data.items.map((project) => (
                <Link key={project.id} className="project-card" to={`/projects/${project.id}`}>
                  <span className="project-icon" aria-hidden="true">
                    ▤
                  </span>
                  <h2>{project.name}</h2>
                  <p>
                    {project.description || 'No description yet. Every project starts somewhere.'}
                  </p>
                  <span className="card-footer">
                    Open project <span aria-hidden="true">↗</span>
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <Empty title="Start with a project.">
              A website, a side project, a big idea. Give it a home and take the first step.
            </Empty>
          )}
          <Pagination
            offset={offset}
            limit={12}
            total={projects.data.total}
            onChange={(next) => setParams({ offset: String(next) })}
          />
        </>
      )}
    </>
  );
}
