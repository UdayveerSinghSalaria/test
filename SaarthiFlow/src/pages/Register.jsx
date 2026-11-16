import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Shield, AlertCircle, Zap, ExternalLink } from 'lucide-react';
import { useAuth } from '../auth.jsx';
import { Card, Title, Page } from '../ui.jsx';

const PROVIDERS = [
  { value: 'gmail', label: 'Gmail', host: 'imap.gmail.com', help: 'https://support.google.com/accounts/answer/185833' },
  { value: 'yahoo', label: 'Yahoo Mail', host: 'imap.mail.yahoo.com', help: 'https://help.yahoo.com/kb/SLN15241.html' },
  { value: 'outlook', label: 'Outlook / Hotmail', host: 'outlook.office365.com', help: 'https://support.microsoft.com/en-us/account-billing/use-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944' }
];

export function Register() {
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    email_provider: 'gmail',
    email_address: '',
    email_app_password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setForm(prev => ({ ...prev, [name]: type === 'checkbox' ? e.target.checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) {
      return setError('Passwords do not match');
    }
    if (form.password.length < 8) {
      return setError('Password must be at least 8 characters');
    }
    if (form.email_app_password.length < 16) {
      return setError('App Password must be at least 16 characters');
    }
    setLoading(true);
    try {
      await register(form);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectedProvider = PROVIDERS.find(p => p.value === form.email_provider);

  return (
    <Page title="Create Account" sub="Set up SaarthiFlow with your email for AI-powered inbox analysis">
      <Card className="max-w-2xl mx-auto">
        <Title icon={Zap}>Register</Title>
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-50 text-rose-600 text-sm flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Account Info */}
          <Card className="bg-brand-50/30">
            <Title icon={Shield}>Account Information</Title>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold block mb-1">Name</span>
                <input
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  className="inp"
                  required
                  placeholder="Your name"
                  autoComplete="name"
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold block mb-1">Email</span>
                <input
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  className="inp"
                  required
                  placeholder="you@domain.com"
                  autoComplete="email"
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold block mb-1">Password</span>
                <input
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  className="inp"
                  required
                  minLength={8}
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold block mb-1">Confirm Password</span>
                <input
                  name="confirmPassword"
                  type="password"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  className="inp"
                  required
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </label>
            </div>
          </Card>

          {/* Email Configuration */}
          <Card className="bg-emerald-50/30">
            <Title icon={Mail}>Email for AI Inbox Analysis</Title>
            <p className="text-sm text-ink/60 mb-4">
              Enable 2FA on your email, then generate an{' '}
              <a href={selectedProvider?.help} target="_blank" rel="noopener noreferrer" className="underline">
                App Password
              </a>{' '}
              (not your regular password). SaarthiFlow uses IMAP to read emails and SMTP to send replies.
              <br />
              <span className="text-xs text-ink/50">Your app password is encrypted and never shared.</span>
            </p>
            <div className="space-y-4">
              <label className="block">
                <span className="text-sm font-semibold block mb-1">Email Provider</span>
                <select
                  name="email_provider"
                  value={form.email_provider}
                  onChange={handleChange}
                  className="inp"
                >
                  {PROVIDERS.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-semibold block mb-1">Your Email Address</span>
                <input
                  name="email_address"
                  type="email"
                  value={form.email_address}
                  onChange={handleChange}
                  className="inp"
                  required
                  placeholder="your@email.com"
                />
              </label>
              <label className="block">
                <span className="text-sm font-semibold block mb-1">App Password</span>
                <input
                  name="email_app_password"
                  type="password"
                  value={form.email_app_password}
                  onChange={handleChange}
                  className="inp"
                  required
                  minLength={16}
                  placeholder="abcd efgh ijkl mnop (16+ chars)"
                  autoComplete="off"
                />
              </label>
            </div>
          </Card>

          <button className="btn w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-ink/60">
          Already have an account? <Link to="/login" className="text-brand-600 font-semibold">Sign In</Link>
        </p>
      </Card>
    </Page>
  );
}