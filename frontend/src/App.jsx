import React, { useState, useEffect } from 'react';
import { Routes, Route, NavLink, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { Home, Bot, FolderKanban, CheckSquare, Activity as Act, CalendarDays, Zap, BarChart3, Settings as Cog, Puzzle, Search, Bell, Menu, X, ChevronDown, Loader2 } from 'lucide-react';
import { useApp } from './store.jsx';
import * as P from './pages.jsx';

export default function App() {
  const { proposals, settings, loading, authRequired, error } = useApp();
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  const nav = useNavigate();
  const [q, setQ] = useState('');

  const pend = proposals.filter(p => p.status === 'pending').length;
  useEffect(() => { setOpen(false); window.scrollTo(0, 0) }, [loc.pathname]);

  const main = [['/', 'Overview', Home], ['/agent', 'Agent Studio', Bot], ['/space', 'My Space', FolderKanban], ['/approvals', 'Approvals', CheckSquare], ['/activity', 'Activity', Act]];
  const tools = [['/calendar', 'Calendar View', CalendarDays], ['/quick-actions', 'Quick Actions', Zap], ['/analytics', 'Analytics', BarChart3]];
  const foot = [['/settings', 'Settings', Cog], ['/extension', 'Get Extension', Puzzle]];

  const Link = ({ to, label, Icon }) => (
    <NavLink
      key={to}
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        'flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] font-medium transition ' +
        (isActive ? 'text-white shadow-lg' : 'text-ink/80 hover:bg-white/70')
      }
      style={({ isActive }) => isActive ? { background: 'linear-gradient(135deg,#a78bfa,#8b5cf6)' } : {}}
    >
      <Icon size={20} />
      {label}
      {to === '/approvals' && pend > 0 && (
        <span className="ml-auto grid h-6 w-6 place-items-center rounded-full bg-brand-500 text-xs font-bold text-white">
          {pend}
        </span>
      )}
    </NavLink>
  );

  const side = (
    <div className="flex h-full flex-col gap-1 p-4">
      <div className="mb-5 flex items-center gap-2 px-2">
        <div className="grid h-10 w-10 place-items-center rounded-2xl text-white" style={{ background: 'linear-gradient(135deg,#8b5cf6,#6d28d9)' }}>
          <Zap size={22} />
        </div>
        <div>
          <div className="text-xl font-extrabold italic leading-5">SaarthiFlow</div>
          <div className="text-xs text-ink/60">From Browsing to Doing</div>
        </div>
      </div>
      {main.map(([to, label, Icon]) => <Link key={to} to={to} label={label} Icon={Icon} />)}
      <div className="mt-4 border-t border-brand-100 px-3 pb-1 pt-4 text-sm font-semibold text-ink/60">Tools</div>
      {tools.map(([to, label, Icon]) => <Link key={to} to={to} label={label} Icon={Icon} />)}
      <div className="mt-auto space-y-1">{foot.map(([to, label, Icon]) => <Link key={to} to={to} label={label} Icon={Icon} />)}</div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="grid h-12 w-12 place-items-center rounded-2xl text-white" style={{ background: 'linear-gradient(135deg,#8b5cf6,#6d28d9)' }}>
            <Zap size={22} />
          </div>
          <p className="text-sm text-ink/60">Loading SaarthiFlow…</p>
        </div>
      </div>
    );
  }

  if (authRequired) return <AuthPage />;

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-white/70 bg-white/50 backdrop-blur-xl lg:block">{side}</aside>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink/30" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white/95 backdrop-blur-xl">
            <button className="absolute right-3 top-3" onClick={() => setOpen(false)} aria-label="Close menu"><X /></button>
            {side}
          </aside>
        </div>
      )}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center gap-3 px-4 py-3 md:px-8">
          <button className="glass !rounded-xl p-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu /></button>
          <form className="glass !rounded-full ml-auto flex max-w-md flex-1 items-center gap-2 px-4 py-2" onSubmit={e => { e.preventDefault(); nav('/space?q=' + encodeURIComponent(q)) }}>
            <Search size={18} className="text-ink/50" />
            <input value={q} onChange={e => setQ(e.target.value)} className="w-full bg-transparent text-sm outline-none" placeholder="Search tasks…" />
          </form>
          <button className="glass relative !rounded-full p-2.5" onClick={() => nav('/approvals')} aria-label="Approvals"><Bell size={20} />{pend > 0 && <i className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-brand-500" />}</button>
          <NavLink to="/settings" className="flex items-center gap-1"><span className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-brand-700 font-bold text-white">{settings?.name?.[0] || 'U'}</span><ChevronDown size={16} /></NavLink>
        </header>
        {error && <p role="alert" className="mx-4 mt-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700 md:mx-8">{error}</p>}
        <main className="px-4 pb-10 md:px-8">
          <Routes>
            <Route path="/" element={<P.Overview />} />
            <Route path="/agent" element={<P.Agent />} />
            <Route path="/space" element={<P.Space />} />
            <Route path="/approvals" element={<P.Approvals />} />
            <Route path="/activity" element={<P.ActivityPage />} />
            <Route path="/calendar" element={<P.CalendarPage />} />
            <Route path="/quick-actions" element={<P.Quick />} />
            <Route path="/analytics" element={<P.Analytics />} />
            <Route path="/settings" element={<P.SettingsPage />} />
            <Route path="/extension" element={<P.Extension />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function AuthPage() {
  const { signIn, signUp } = useApp();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (mode === 'login') await signIn(email, password);
      else await signUp(email, password, name);
    } catch (err) {
      setError(err.message || 'Unable to authenticate.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <form onSubmit={submit} className="glass w-full max-w-sm space-y-4 p-6">
        <div className="text-center">
          <h1 className="text-2xl font-extrabold">SaarthiFlow</h1>
          <p className="mt-1 text-sm text-ink/60">{mode === 'login' ? 'Sign in to your workspace' : 'Create your account'}</p>
        </div>
        {mode === 'signup' && <input className="inp" value={name} onChange={e => setName(e.target.value)} placeholder="Your name" autoComplete="name" />}
        <input className="inp" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" autoComplete="email" />
        <input className="inp" type="password" required minLength={mode === 'signup' ? 8 : 1} value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} />
        {error && <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <button className="btn w-full" type="submit" disabled={submitting}>
          {submitting && <Loader2 size={16} className="animate-spin" />}
          {mode === 'login' ? 'Sign in' : 'Create account'}
        </button>
        <p className="text-center text-sm text-ink/60">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button type="button" className="font-semibold text-brand-700 underline" onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); }}>
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </form>
    </div>
  );
}