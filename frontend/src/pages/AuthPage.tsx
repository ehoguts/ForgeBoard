import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import type { User } from '../api';
import { ErrorNotice } from '../components/Feedback';
import { discardPrivateQueries } from '../session';

export function AuthPage({ register = false, user }: { register?: boolean; user?: User | null }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: async () => {
      if (register) {
        await api.register({ email, password });
        return null;
      }
      return api.login({ email, password });
    },
    onSuccess: (result) => {
      setPassword('');
      if (register) navigate('/login?registered=1');
      else {
        discardPrivateQueries(client);
        client.setQueryData(['me'], result);
        navigate('/');
      }
    },
  });
  if (user) return <Navigate to="/" replace />;
  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }
  return (
    <main className="auth-shell">
      <section className="auth-story">
        <Link to="/" className="brand">
          <span className="brand-symbol">F</span>ForgeBoard
        </Link>
        <div>
          <span className="eyebrow">A little structure. A lot of progress.</span>
          <h1>
            Good work starts
            <br />
            with a clear
            <br />
            <em>next step.</em>
          </h1>
          <p>A focused home for your projects and the issues that move them forward.</p>
        </div>
        <span className="story-footer">Built for makers. Made for momentum.</span>
      </section>
      <section className="auth-panel">
        <form className="auth-form" onSubmit={submit}>
          <span className="eyebrow">YOUR PERSONAL WORKSPACE</span>
          <h2>{register ? 'Start building.' : 'Welcome back.'}</h2>
          <p className="muted">
            {register
              ? 'Create an account to make progress visible.'
              : 'Sign in and pick up where you left off.'}
          </p>
          {params.has('registered') && !register && (
            <p className="notice success" role="status">
              Account created. Sign in to your workspace.
            </p>
          )}
          <ErrorNotice error={mutation.error} />
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              required
              maxLength={254}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete={register ? 'new-password' : 'current-password'}
              required
              minLength={register ? 12 : 1}
              maxLength={128}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {register && (
            <small className="muted">Use 12–128 characters. A unique passphrase works well.</small>
          )}
          <button className="button auth-submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Please wait…' : register ? 'Create account →' : 'Sign in →'}
          </button>
          <p className="auth-switch">
            {register ? 'Already have an account?' : 'New to ForgeBoard?'}{' '}
            <Link to={register ? '/login' : '/register'}>
              {register ? 'Sign in' : 'Create an account'}
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}
