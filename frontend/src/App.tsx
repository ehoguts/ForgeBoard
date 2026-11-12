import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { ApiError, api } from './api';
import { Loading, ErrorNotice } from './components/Feedback';
import { AuthPage } from './pages/AuthPage';
import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { ProjectDetail } from './pages/ProjectDetail';
import { discardPrivateQueries } from './session';

export function App() {
  const client = useQueryClient();
  useEffect(() => {
    function expireSession() {
      discardPrivateQueries(client);
      client.setQueryData(['me'], null);
    }
    window.addEventListener('forgeboard:session-expired', expireSession);
    return () => window.removeEventListener('forgeboard:session-expired', expireSession);
  }, [client]);
  const me = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      try {
        return await api.me();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
  });
  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: () => {
      discardPrivateQueries(client);
      client.setQueryData(['me'], null);
    },
  });
  if (me.isPending)
    return (
      <div className="initial-loading">
        <Loading />
      </div>
    );
  if (me.isError)
    return (
      <main className="initial-loading">
        <ErrorNotice error={me.error} retry={() => void me.refetch()} />
      </main>
    );
  if (!me.data)
    return (
      <Routes>
        <Route path="/register" element={<AuthPage register />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link className="brand" to="/">
          <span className="brand-symbol">F</span>ForgeBoard<span className="brand-dot">.</span>
        </Link>
        <span className="nav-label">WORKSPACE</span>
        <nav aria-label="Main navigation">
          <NavLink to="/" end>
            <span aria-hidden="true">▦</span>Overview
          </NavLink>
          <NavLink to="/projects">
            <span aria-hidden="true">▤</span>Projects
          </NavLink>
        </nav>
        <div className="sidebar-note">
          <span aria-hidden="true">✦</span>
          <p>
            Big ideas.
            <br />
            <strong>Small, steady steps.</strong>
          </p>
        </div>
        <div className="account">
          <span className="avatar" aria-hidden="true">
            {me.data.email[0].toUpperCase()}
          </span>
          <div>
            <span className="account-email" title={me.data.email}>
              {me.data.email}
            </span>
            <span className="muted small-text">Personal workspace</span>
          </div>
        </div>
        <button
          className="logout-button"
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          {logout.isPending ? 'Signing out…' : 'Sign out ↗'}
        </button>
        <ErrorNotice error={logout.error} />
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>YOUR PERSONAL WORKSPACE</span>
          <span className="local-badge">
            <i className="dot done" />
            Focused on what’s next
          </span>
        </header>
        <main id="main-content" className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="/register" element={<Navigate to="/" replace />} />
            <Route
              path="*"
              element={
                <>
                  <h1>Page not found.</h1>
                  <p>Let’s get you back to your workspace.</p>
                  <Link className="button" to="/">
                    Go to overview
                  </Link>
                </>
              }
            />
          </Routes>
        </main>
        <footer className="app-footer">
          ForgeBoard <span>Make progress visible.</span>
        </footer>
      </div>
    </div>
  );
}
