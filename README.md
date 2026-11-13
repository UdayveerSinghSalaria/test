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
| Gmail read (latest 5, search, detail, load-more) | ✅ Live* | real Gmail API, multipart decoding, sanitized HTML |
| Disconnect | ✅ Live* | deletes stored credentials |
| Tasks (CRUD, user-scoped) | ✅ Live | |
| Approvals (human-in-the-loop gate) | ✅ Live | agent `create_task` blocks until approved |
| Activity audit log | ✅ Live | tool calls/plans/approvals; **never email bodies** |
| AI Assistant (LangGraph loop) | ✅ Live* | streamed plan → tools → answer; needs `LLM_*` env |
| Calendar | 🚧 Placeholder | intentionally labeled "Not implemented" |
| Gmail send / draft | ❌ Not requested | readonly scope only, per spec |
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
npm run dev          # http://localhost:3000
```

The frontend proxies `/api/*` to FastAPI (see `next.config.ts`), so the
browser only ever talks to one origin and the session cookie stays same-site.

### 3. Run tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

32 tests cover: session/crypto primitives, HTML sanitization, multipart email
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
| `CORS_ORIGINS` | optional | defaults to `http://localhost:3000` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | for Gmail | OAuth client from Google Cloud Console |
| `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` | for agent | any OpenAI-compatible endpoint or Anthropic |

### Google Cloud setup (the one manual step)

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials).
2. Create project → enable the **Gmail API**.
3. Configure the OAuth consent screen (External + test users is fine).
4. Create an **OAuth 2.0 Client ID** (Web application) with authorized redirect URI:
   `http://localhost:8000/api/integrations/google/callback`
5. Put the client id/secret into `backend/.env`.

Requested scopes (nothing more): `openid`, `email`, `profile`,
`https://www.googleapis.com/auth/gmail.readonly` — **no send/write scope is
requested in this milestone.**

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

Open http://localhost:3000 → create an account → **Integrations → Connect
Gmail** → Google consent screen → back → **Inbox** shows your 5 latest real
emails.
