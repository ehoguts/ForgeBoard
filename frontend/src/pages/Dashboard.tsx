import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import { Empty, ErrorNotice, Loading } from '../components/Feedback';

export function Dashboard() {
  const summary = useQuery({ queryKey: ['summary'], queryFn: api.summary });
  const projects = useQuery({ queryKey: ['projects', 0], queryFn: () => api.projects() });
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">YOUR WORK, AT A GLANCE</span>
          <h1>Make room for progress.</h1>
          <p>Small steps add up. Here’s where things stand.</p>
        </div>
        <Link className="button" to="/projects?new=1">
          + New project
        </Link>
      </header>
      {summary.isPending ? (
        <Loading />
      ) : summary.isError ? (
        <ErrorNotice error={summary.error} retry={() => void summary.refetch()} />
      ) : (
        <>
          <div className="stats-grid">
            <article className="stat primary-stat">
              <span>Projects</span>
              <strong>{summary.data.project_count}</strong>
              <span className="stat-foot">
                Ideas taking shape <span aria-hidden="true">↗</span>
              </span>
            </article>
            <article className="stat">
              <span>Total issues</span>
              <strong>{summary.data.total_issues}</strong>
              <span className="stat-foot">Every next step, in one place</span>
            </article>
            <article className="stat">
              <span>In progress</span>
              <strong>{summary.data.in_progress}</strong>
              <span className="stat-foot">
                <i className="dot in_progress" />
                Work in motion
              </span>
            </article>
            <article className="stat">
              <span>Done</span>
              <strong>{summary.data.done}</strong>
              <span className="stat-foot">
                <i className="dot done" />
                Progress worth celebrating
              </span>
            </article>
          </div>
          <section className="panel status-overview">
            <div>
              <span className="eyebrow">ISSUE BREAKDOWN</span>
              <h2>A clear view of the work.</h2>
            </div>
            <div className="status-totals">
              <span>
                <i className="dot todo" />
                To do <strong>{summary.data.todo}</strong>
              </span>
              <span>
                <i className="dot in_progress" />
                In progress <strong>{summary.data.in_progress}</strong>
              </span>
              <span>
                <i className="dot done" />
                Done <strong>{summary.data.done}</strong>
              </span>
            </div>
          </section>
        </>
      )}
      <section className="section-block">
        <div className="section-heading">
          <h2>Your recent projects</h2>
          <Link to="/projects">View all projects ↗</Link>
        </div>
        {projects.isPending ? (
          <Loading />
        ) : projects.isError ? (
          <ErrorNotice error={projects.error} retry={() => void projects.refetch()} />
        ) : projects.data.items.length ? (
          <div className="project-grid">
            {projects.data.items.slice(0, 3).map((project) => (
              <Link className="project-card" key={project.id} to={`/projects/${project.id}`}>
                <span className="project-icon" aria-hidden="true">
                  ▤
                </span>
                <h3>{project.name}</h3>
                <p>
                  {project.description || 'A fresh start. Add your first issue and get moving.'}
                </p>
                <span className="card-footer">
                  Open project <span aria-hidden="true">↗</span>
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <Empty title="Your next idea belongs here.">
            Create your first project, then turn the work into small, actionable issues.
          </Empty>
        )}
      </section>
    </>
  );
}
