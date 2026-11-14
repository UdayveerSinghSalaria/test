import React, { useEffect, useState } from 'react';
import { AlertCircle, Mail, RefreshCw, Search, Send, Unplug } from 'lucide-react';
import { api } from './api.js';
import { Card, Empty, Page } from './ui.jsx';

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ''
    : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export default function MailPage() {
  const [connection, setConnection] = useState(undefined);
  const [emails, setEmails] = useState([]);
  const [nextPageToken, setNextPageToken] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState(() => {
    const status = new URLSearchParams(window.location.search).get('status');
    if (status === 'connected') return 'Gmail connected. Your inbox is ready.';
    if (status === 'error') return 'Google could not connect your account. Please try again.';
    return '';
  });
  const [compose, setCompose] = useState(false);

  async function loadEmails({ search = '', pageToken = null, append = false } = {}) {
    setError('');
    setBusy(true);
    try {
      const result = await api.getEmails({
        limit: 20,
        q: search ? `in:inbox ${search}` : 'in:inbox',
        ...(pageToken ? { page_token: pageToken } : {}),
      });
      setEmails(current => append ? [...current, ...result.emails] : result.emails);
      setNextPageToken(result.next_page_token);
      if (!append) setSelected(null);
    } catch (err) {
      setError(err.message || 'Could not load Gmail.');
    } finally {
      setBusy(false);
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    async function checkConnection() {
      try {
        const sharedMailbox = await api.getActivepiecesStatus();
        if (!active) return;
        if (sharedMailbox) {
          setConnection(sharedMailbox);
          await loadEmails();
          return;
        }
        const status = await api.getGoogleStatus();
        if (!active) return;
        setConnection(status);
        if (status) {
          await loadEmails();
          return;
        }
        setLoading(false);
      } catch (err) {
        if (!active) return;
        setError(err.message || 'Could not check the Google connection.');
        setLoading(false);
      }
    }
    checkConnection();
    return () => { active = false; };
  }, []);

  async function openEmail(id) {
    setError('');
    setBusy(true);
    try {
      setSelected(await api.getEmail(id));
    } catch (err) {
      setError(err.message || 'Could not open this email.');
    } finally {
      setBusy(false);
    }
  }

  async function submitSearch(event) {
    event.preventDefault();
    await loadEmails({ search: query.trim() });
  }

  async function sendMessage(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await api.sendEmail({
        to: data.get('to'),
        subject: data.get('subject'),
        body: data.get('body'),
      });
      setNotice('Email sent.');
      form.reset();
      setCompose(false);
      await loadEmails({ search: query.trim() });
    } catch (err) {
      setError(err.message || 'Could not send this email.');
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    if (!window.confirm(`Disconnect ${connection?.provider_email || 'your Google account'}?`)) return;
    setError('');
    setBusy(true);
    try {
      await api.disconnectGoogle();
      setConnection(null);
      setEmails([]);
      setSelected(null);
      setNotice('Google account disconnected.');
    } catch (err) {
      setError(err.message || 'Could not disconnect Google.');
    } finally {
      setBusy(false);
    }
  }

  const isActivepiecesMailbox = connection?.provider === 'activepieces';
  const canSend = !isActivepiecesMailbox && connection?.scopes?.includes('https://www.googleapis.com/auth/gmail.send');

  if (loading) {
      return <Page title="Mail" sub="Your connected mailbox."><Card>Loading your email connection…</Card></Page>;
  }

  if (!connection) {
    return (
      <Page title="Mail" sub="Connect your own mailbox">
        {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <Card className="max-w-2xl space-y-3">
          <div className="flex items-center gap-3"><Mail className="text-brand-600" size={24}/><h2 className="text-lg font-bold">Your mailbox is not configured for this account</h2></div>
          <p className="text-sm text-ink/65">Connect your own Gmail account in the Activepieces Search/Get flows. Render must have ACTIVEPIECES_API_KEY, ACTIVEPIECES_SEARCH_FLOW_ID, ACTIVEPIECES_GET_FLOW_ID, and ACTIVEPIECES_ALLOWED_USER_EMAIL configured.</p>
          <p className="text-sm text-ink/65">Agent Studio can draft email text in chat. Sending requires a configured Activepieces send flow and your approval.</p>
        </Card>
      </Page>
    );
  }

  return (
    <Page
      title="Mail"
      sub={isActivepiecesMailbox ? connection.mailbox : `Connected as ${connection.provider_email || 'Google account'}`}
      right={<div className="flex flex-wrap gap-2">
        <button className="btn2" disabled={busy} onClick={() => loadEmails({ search: query.trim() })}><RefreshCw size={16}/>Refresh</button>
        {!isActivepiecesMailbox && <button className="btn2 !text-rose-700" disabled={busy} onClick={disconnect}><Unplug size={16}/>Disconnect</button>}
      </div>}
    >
      {notice && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p>}
      {error && <p role="alert" className="flex items-center gap-2 rounded-xl bg-rose-50 p-3 text-sm text-rose-700"><AlertCircle size={16}/>{error}</p>}
      {isActivepiecesMailbox && <Card className="text-sm text-ink/70">
        This is your Activepieces-connected mailbox, available only to the allowlisted SaarthiFlow account. Use Agent Studio to draft or prepare email; sending requires your explicit approval.
      </Card>}
      {!isActivepiecesMailbox && !canSend && <Card className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink/70">Reconnect Google and approve the Gmail send permission to compose and send mail.</p>
        <a className="btn2" href={api.googleConnectUrl()}>Grant send access</a>
      </Card>}
      {canSend && <div className="flex justify-end"><button className="btn" onClick={() => setCompose(value => !value)}><Send size={16}/>{compose ? 'Close composer' : 'Compose'}</button></div>}
      {compose && canSend && <Card>
        <h2 className="mb-3 text-lg font-bold">New email</h2>
        <form className="space-y-3" onSubmit={sendMessage}>
          <label className="block text-sm font-semibold">To<input className="inp mt-1" name="to" type="email" required maxLength={320} placeholder="recipient@example.com"/></label>
          <label className="block text-sm font-semibold">Subject<input className="inp mt-1" name="subject" maxLength={998} placeholder="Subject"/></label>
          <label className="block text-sm font-semibold">Message<textarea className="inp mt-1 min-h-36 resize-y" name="body" required maxLength={100000} placeholder="Write your email…"/></label>
          <button className="btn" type="submit" disabled={busy}><Send size={16}/>{busy ? 'Sending…' : 'Send email'}</button>
        </form>
      </Card>}
      <form className="flex gap-2" onSubmit={submitSearch}>
        <div className="glass flex min-w-0 flex-1 items-center gap-2 rounded-xl px-3">
          <Search size={18} className="shrink-0 text-ink/50"/>
          <input className="w-full bg-transparent py-2 text-sm outline-none" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search Gmail (e.g. from:someone@example.com)"/>
        </div>
        <button className="btn2" type="submit" disabled={busy}>Search</button>
      </form>
      <div className="grid gap-4 xl:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.2fr)]">
        <Card className="min-w-0 space-y-2">
          <h2 className="font-bold">Inbox</h2>
          {!emails.length ? <Empty text={busy ? 'Loading messages…' : 'No messages found.'}/> : emails.map(email =>
            <button key={email.id} className={'w-full rounded-xl border p-3 text-left transition hover:bg-brand-50 ' + (selected?.id === email.id ? 'border-brand-400 bg-brand-50' : 'border-brand-100 bg-white/70')} onClick={() => openEmail(email.id)}>
              <span className="flex items-start justify-between gap-2"><b className="truncate text-sm">{email.sender_name || email.sender_email}</b><span className="shrink-0 text-xs text-ink/50">{formatDate(email.received_at)}</span></span>
              <span className="mt-1 block truncate text-sm font-semibold">{email.subject || '(no subject)'}</span>
              <span className="mt-1 block line-clamp-2 text-xs text-ink/60">{email.snippet}</span>
            </button>
          )}
          {nextPageToken && <button className="btn2 w-full" disabled={busy} onClick={() => loadEmails({ search: query.trim(), pageToken: nextPageToken, append: true })}>Load more</button>}
        </Card>
        <Card className="min-h-64 min-w-0">
          {!selected ? <Empty text="Select a message to read it."/> : <article className="space-y-3">
            <h2 className="break-words text-xl font-bold">{selected.subject || '(no subject)'}</h2>
            <div className="border-b border-brand-100 pb-3 text-sm text-ink/60">
              <p>From: {selected.sender_name} {selected.sender_email && `<${selected.sender_email}>`}</p>
              <p>To: {selected.to?.map(address => address.address).join(', ')}</p>
              <p>{formatDate(selected.received_at)}</p>
            </div>
            <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-6">{selected.body_text || 'This message has no plain-text body.'}</pre>
          </article>}
        </Card>
      </div>
    </Page>
  );
}
