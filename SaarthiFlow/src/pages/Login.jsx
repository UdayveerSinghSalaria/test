import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, AlertCircle, Zap } from 'lucide-react';
import { useAuth } from '../auth.jsx';
import { Card, Title, Page } from '../ui.jsx';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Page title="Welcome back" sub="Sign in to your SaarthiFlow account">
      <Card className="max-w-md mx-auto">
        <Title icon={Zap}>Sign In</Title>
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 text-rose-600 text-sm flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" size={18} />
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="inp pl-10"
                required
                autoComplete="email"
                placeholder="you@domain.com"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" size={18} />
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="inp pl-10"
                required
                autoComplete="current-password"
                placeholder="••••••••"
              />
            </div>
          </div>
          <button className="btn w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-ink/60">
          Don't have an account? <Link to="/register" className="text-brand-600 font-semibold">Create one</Link>
        </p>
      </Card>
    </Page>
  );
}