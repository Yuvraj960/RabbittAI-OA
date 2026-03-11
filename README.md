# 🐇 Rabbitt AI — Sales Insight Automator

> **Upload a sales CSV/XLSX → AI generates an executive brief → Delivered to your inbox.**

[![CI](https://github.com/YOUR_USERNAME/rabbittai-sales-insight/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/rabbittai-sales-insight/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start via Docker Compose](#quick-start-via-docker-compose)
3. [Manual Local Development](#manual-local-development)
4. [Environment Variables](#environment-variables)
5. [Security Overview](#security-overview)
6. [API Documentation (Swagger)](#api-documentation-swagger)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Deployment](#deployment)
9. [Project Structure](#project-structure)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                                 │
│   Next.js SPA  →  Drag & drop CSV/XLSX  +  recipient email         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ POST /api/analyze
                            │ Header: X-API-Key
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (port 8000)                      │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐  │
│  │ Rate Limiter │   │  API Key     │   │   File Validator      │  │
│  │ (SlowAPI)    │──▶│  Auth Guard  │──▶│   (CSV/XLSX, ≤10MB)  │  │
│  └──────────────┘   └──────────────┘   └──────────┬────────────┘  │
│                                                    │               │
│                              ┌─────────────────────▼───────────┐  │
│                              │   Google Gemini 1.5 Flash API    │  │
│                              │   (AI Executive Summary)         │  │
│                              └──────────────┬──────────────────┘  │
│                                             │                      │
│                              ┌──────────────▼──────────────────┐  │
│                              │   Gmail SMTP (Background Task)   │  │
│                              │   HTML Executive Email           │  │
│                              └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router, TypeScript) |
| Backend | FastAPI (Python 3.11) + Uvicorn |
| AI Engine | Google Gemini 1.5 Flash |
| Email | Gmail SMTP (App Password) |
| Rate Limiting | SlowAPI (10 req/min per IP) |
| Containerization | Docker + docker-compose |
| CI/CD | GitHub Actions |

---

## Quick Start via Docker Compose

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A Gmail account with [App Password](https://myaccount.google.com/apppasswords) enabled
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/rabbittai-sales-insight.git
cd rabbittai-sales-insight
```

### Step 2 — Configure environment variables

```bash
# Copy the template
cp .env.example .env
```

Then open `.env` and fill in all values:

```env
API_SECRET_KEY=your_strong_random_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GMAIL_USER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
NEXT_PUBLIC_API_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000
```

> **Tip:** Generate a strong `API_SECRET_KEY` with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### Step 3 — Build and run

```bash
docker-compose up --build
```

The first build may take ~3–5 minutes. On subsequent runs, layers are cached.

### Step 4 — Access the app

| Service | URL |
|---------|-----|
| Frontend SPA | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/health |

### Stop the stack

```bash
docker-compose down
```

---

## Manual Local Development

### Backend (FastAPI)

```bash
cd backend

# Create virtualenv
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env in project root (or backend/), then run:
uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_API_KEY=your_api_secret_key

npm run dev      # → http://localhost:3000
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full reference.

| Variable | Required | Description |
|----------|----------|-------------|
| `API_SECRET_KEY` | ✅ | Secret key that clients must send as `X-API-Key` header |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key from [AI Studio](https://aistudio.google.com) |
| `GMAIL_USER` | ✅ | Gmail address used as the sender |
| `GMAIL_APP_PASSWORD` | ✅ | 16-char Gmail App Password (**not** your login password) |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend base URL (e.g., `http://localhost:8000` or Render URL) |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins (e.g., `http://localhost:3000`) |

---

## Security Overview

We interpret "secured endpoints" across multiple defense layers:

| Layer | Mechanism | Detail |
|-------|-----------|--------|
| **Authentication** | API Key via `X-API-Key` header | All `/api/*` routes require a valid key. Returns `403 Forbidden` on mismatch |
| **Rate Limiting** | SlowAPI (token bucket) | `/api/analyze` limited to **10 requests/minute** per client IP. Returns `429 Too Many Requests` |
| **CORS** | Strict allowlist | Only origins listed in `ALLOWED_ORIGINS` can make cross-origin requests |
| **File Validation** | Extension + size checks | Only `.csv`, `.xlsx`, `.xls` accepted. Files larger than **10MB** are rejected with `413` |
| **Container Security** | Non-root Docker user | Both backend and frontend containers run as unprivileged `appuser`/`nextjs` |
| **Secret Management** | Environment variables only | No secrets are committed to the repository. All configuration via `.env` |
| **HTTP Security Headers** | Next.js config | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection` |

---

## API Documentation (Swagger)

The live Swagger UI is available at **`http://localhost:8000/docs`** (or your Render URL + `/docs`).

### Using Swagger UI

1. Open `/docs` in your browser
2. Click the **Authorize 🔒** button (top right)
3. Enter your `API_SECRET_KEY` value
4. Click **Authorize**, then close
5. Expand the `POST /api/analyze` endpoint → **Try it out**
6. Upload a CSV file and enter an email → **Execute**

### Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/` | Service info and links | No |
| `GET` | `/api/health` | Health check (used by Docker) | No |
| `POST` | `/api/analyze` | Upload file, generate summary, send email | **Yes** |
| `GET` | `/docs` | Swagger UI | No |
| `GET` | `/openapi.json` | Raw OpenAPI schema | No |

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) triggers on **every Pull Request to `main`** and on **direct pushes to `main`**.

### Jobs

| Job | Steps |
|-----|-------|
| `backend-lint-build` | Python 3.11 install → `ruff check` linting → `docker build ./backend` |
| `frontend-lint-build` | Node 20 → `npm ci` → `next lint` → `next build` → `docker build ./frontend` |

Both jobs run **in parallel** for faster feedback.

---

## Deployment

### Frontend → Vercel

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import this repo
3. Set **Root Directory** to `frontend`
4. Add environment variables in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL` → your Render backend URL
   - `NEXT_PUBLIC_API_KEY` → your `API_SECRET_KEY`
5. Deploy

### Backend → Render

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect this GitHub repo
3. Set **Root Directory** to `backend`
4. Runtime: **Docker**
5. Add all environment variables from `.env.example`
6. Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
7. Deploy

> **Important:** After deploying, update `ALLOWED_ORIGINS` on Render to include your Vercel frontend URL.

---

## Project Structure

```
rabbittai-sales-insight/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI/CD
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic settings (reads .env)
│   │   │   └── security.py      # X-API-Key auth dependency
│   │   ├── routers/
│   │   │   └── analyze.py       # POST /api/analyze endpoint
│   │   ├── services/
│   │   │   ├── ai_service.py    # Google Gemini integration
│   │   │   ├── email_service.py # Gmail SMTP delivery
│   │   │   └── file_service.py  # CSV/XLSX parsing & validation
│   │   └── main.py              # FastAPI app, middleware, routes
│   ├── Dockerfile               # Multi-stage, non-root user
│   ├── pyproject.toml           # Ruff linter config
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── globals.css          # Premium dark-mode design system
│   │   ├── layout.tsx           # Root layout + SEO metadata
│   │   └── page.tsx             # Main SPA (upload → feedback)
│   ├── Dockerfile               # 3-stage Next.js standalone build
│   ├── next.config.js           # Standalone output + security headers
│   └── package.json
├── sample_data/
│   └── sales_q1_2026.csv        # Reference data for testing
├── .env.example                 # Template for all env variables
├── .gitignore
├── docker-compose.yml           # Full stack orchestration
└── README.md                    # This file
```

---

## Testing the Full Flow

1. Start the stack: `docker-compose up --build`
2. Open http://localhost:3000
3. Drag and drop `sample_data/sales_q1_2026.csv` into the upload zone
4. Enter your email address
5. Click **Generate & Send Report**
6. Watch the animated progress steps in the UI
7. Check your inbox for the AI-generated HTML executive summary
8. Verify Swagger at http://localhost:8000/docs

---

## License

Private — Internal use at Rabbitt AI. Not licensed for redistribution.
