# AI Work Assistant — MVP Preview

> **Temporary neutral title.** The product name has not been decided. The
> application name lives in **one place** (`frontend/lib/config.ts` →
> `APP_NAME`, and `backend/.env` → `APP_NAME`) — change it there and the whole
> app follows. No logo or permanent branding exists yet, by design.

An agentic personal work assistant: connect a Google account, read the real
Gmail inbox, and hand natural-language instructions to an agent that plans,
calls permission-controlled tools, and asks before it changes anything.

**Stack:** Next.js 16 · React 19 · TypeScript · Tailwind v4 · shadcn/ui ·
FastAPI · Pydantic · SQLAlchemy 2 · LangGraph · PostgreSQL (Supabase-ready,
SQLite for local dev)

---

## What works today

| Area | Status | Notes |
|---|---|---|
| Email/password auth | ✅ Live | argon2 hashes, httpOnly signed session cookie |
| Google OAuth 2.0 | ✅ Live* | full Authorization Code Flow, state CSRF, encrypted tokens |
| Gmail inbox (per-user, search, detail, load-more) | ✅ Live* | real Gmail API, multipart decoding, sanitized text |
| Gmail send | ✅ Live* | explicit plain-text compose action; Gmail send permission |
| Disconnect | ✅ Live* | deletes stored credentials |
| Tasks (CRUD, user-scoped) | ✅ Live | |
| Approvals (human-in-the-loop gate) | ✅ Live | agent `create_task` blocks until approved |
| Activity audit log | ✅ Live | tool calls/plans/approvals; **never email bodies** |
| AI Assistant (LangGraph loop) | ✅ Live* | streamed plan → tools → answer; needs `LLM_*` env |
| Calendar | 🚧 Placeholder | intentionally labeled "Not implemented" |
| Gmail drafts | ❌ Not implemented | |
| Google Calendar API | ❌ Prepared, not wired | |

\* requires environment credentials — see [Configuration](#configuration).

Nothing on any page is mocked: pages without backend support say so plainly.

---

## Quick start

### Prerequisites

- Node.js 20+
- Python 3.11+ (tested on 3.14)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate.ps1          # Windows (use `source .venv/bin/activate` elsewhere)
pip install -r requirements.txt

# Create your environment file
copy .env.example .env
# Then generate the two REQUIRED secrets (app refuses to start without them):
python -c "import secrets; print(secrets.token_urlsafe(48))"       # -> SESSION_SECRET
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # -> CREDENTIALS_ENCRYPTION_KEY

uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev          # Vite prints the local URL (usually http://localhost:5173)
```

### 3. Deploy the app

The Netlify site serves the Vite frontend and proxies `/api/*` to the FastAPI
backend through a Netlify Function, keeping session cookies same-site.

1. Create a Supabase Postgres database and deploy this repository to Render
   using `render.yaml`.
2. In Render, set `DATABASE_URL` to the Supabase connection string using the
   `postgresql+psycopg://` driver, set `BACKEND_URL` to the Render service URL,
   and provide a valid `CREDENTIALS_ENCRYPTION_KEY`. Render generates
   `SESSION_SECRET`.
3. In Netlify, set `BACKEND_API_URL` to the Render URL ending in `/api`, then
   trigger a new deploy. If your Netlify site uses a different domain, update
   `CORS_ORIGINS` in Render to include that exact origin.

### 4. Run tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

Tests cover: session/crypto primitives, HTML sanitization, multipart email
decoding, OAuth state CSRF + code exchange, encrypted-at-rest storage, auth
endpoints, task CRUD, **user-level data isolation**, and the approval gate.

---

## Configuration

All secrets live in `backend/.env` (git-ignored; `.env.example` documents
every variable). **The backend fails to start with an actionable message if a
security-critical variable is missing or invalid — it never silently degrades.**

| Variable | Required | Purpose |
|---|---|---|
| `SESSION_SECRET` | ✅ | signs session cookies |
| `CREDENTIALS_ENCRYPTION_KEY` | ✅ | Fernet key; OAuth tokens encrypted at rest |
| `DATABASE_URL` | optional | defaults to local SQLite; use your Supabase Postgres URL in deploy |
| `CORS_ORIGINS` | optional | defaults to local Vite origins |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | for Gmail | OAuth client from Google Cloud Console |
| `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` | for agent | any OpenAI-compatible endpoint or Anthropic |
| `ACTIVEPIECES_API_KEY`, `ACTIVEPIECES_SEARCH_FLOW_ID`, `ACTIVEPIECES_GET_FLOW_ID` | for shared mail | Flow API key and Search/Get flow IDs; all signed-in users share the same read-only mailbox |

### Google Cloud setup (the one manual step)

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials).
2. Create project → enable the **Gmail API**.
3. Configure the OAuth consent screen and add users as test users while the app
   is in testing.
4. Create an **OAuth 2.0 Client ID** (Web application) with authorized
   redirect URIs:
   - Local: `http://localhost:8000/api/integrations/google/callback`
   - Production: `https://testudayrepo.netlify.app/api/integrations/google/callback`

   In production, the callback must use the Netlify domain so the browser sends
   the same-site session and OAuth state cookies through the API proxy.
5. Put the client id/secret into `backend/.env` locally and the Render
   environment variables in production.

Requested scopes: `openid`, `email`, `profile`,
`https://www.googleapis.com/auth/gmail.readonly`, and
`https://www.googleapis.com/auth/gmail.send`. Users must connect their own
Google account from **Mail** and approve both Gmail permissions. Google may
require the OAuth app to be configured/verified for these sensitive scopes;
for an app in testing, only listed test users can connect. Previously connected
users need to reconnect to grant send access.

The Activepieces integration uses one teammate's shared mailbox. When its
three runtime variables are configured, all signed-in users can read and
search that same mailbox. The existing Search/Get flows do not send email.

To configure it in Render, set `ACTIVEPIECES_API_KEY`,
`ACTIVEPIECES_SEARCH_FLOW_ID`, and `ACTIVEPIECES_GET_FLOW_ID`. The backend
uses the project API key and flow IDs; a standalone webhook URL by itself is
not what these settings expect. The Search/Get flow IDs are available from the
teammate's Activepieces project. Keep the API key private.

### Supabase / PostgreSQL

Local dev uses SQLite. For Supabase, set:

```
DATABASE_URL=postgresql+psycopg://postgres.<PROJECT>:<PASSWORD>@aws-0.<REGION>.pooler.supabase.com:6543/postgres
```

(SQLAlchemy models are Postgres-compatible; use Alembic/migrations for
production schema management.)

---

## Architecture

```
frontend/  Next.js app (single origin via /api rewrite proxy)
  app/           login · dashboard · assistant · tasks · inbox · calendar
                  approvals · activity · integrations · settings
  components/    layout (sidebar, shell) + shadcn ui primitives
  lib/           api.ts (central client + NDJSON stream) · auth.ts · config.ts
  types/         mirrors the Pydantic schemas

backend/  FastAPI
  api/           auth · integrations (OAuth) · emails · tasks · approvals
                  activity · assistant (streaming) · deps (auth guard)
  services/      google_oauth (state, exchange, refresh) · gmail_service
                  (list/search/detail, multipart decode, HTML sanitization)
                  token_service (encrypt, auto-refresh, disconnect)
  agents/        planner (structured ExecutionPlan) · orchestrator (LangGraph
                  plan→act→summarize with approval gate) · tools (registry;
                  unknown tools refused) · llm (configurable provider)
  security/      encryption (Fernet) · sessions (signed httpOnly cookies)
  models/        users · integrations · tasks · approvals · activity
```

### Security model

- OAuth entirely backend-side; client secret and refresh tokens never reach
  the browser; tokens Fernet-encrypted in the DB.
- CSRF `state` is random, cookie-bound, constant-time compared.
- Session = signed httpOnly SameSite cookie; **nothing auth-related in
  localStorage**.
- Every user-scoped query filters by session `user_id` (tested).
- Email HTML is allowlist-sanitized server-side; raw HTML never rendered.
- Agent may only call registered tools; sensitive tools stop at the approval
  gate; email content is marked untrusted in the system prompt (anti prompt
  injection); audit log stores actions, never message bodies.
- Missing security env vars → startup failure with instructions, never a
  silent downgrade.

---

## How to run it (daily driver)

```powershell
# terminal 1
cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# terminal 2
cd frontend; npm run dev
```

Open the Vite URL (usually http://localhost:5173 or http://localhost:5174),
create an account, then open **Mail → Connect Google account**. After Google
consent, your own Gmail inbox appears in SaarthiFlow.