# HealthOS

Your Personal Health Intelligence Layer — upload lab reports, track nutrition, hydration, sleep, and activity, and get AI-powered health insights tailored for Pakistan.

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+ and npm

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env and set a real SECRET_KEY
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ENVIRONMENT` | No | `development` | Set to `production` to arm the CORS wildcard guard |
| `DATABASE_URL` | No | `sqlite:///./healthos.db` | Postgres example: `postgresql://user:pass@host/db` |
| `SECRET_KEY` | **Yes** | — | Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `10080` | Token lifetime (7 days) |
| `CORS_ORIGINS` | **Yes in prod** | localhost list | Exact frontend origin, comma-separated, no `*` |
| `AI_PROVIDER` | No | `mock` | `mock` needs no key; set `qwen` for Qwen |
| `QWEN_API_KEY` | Only if AI_PROVIDER=qwen | — | Qwen API key |
| `QWEN_MODEL` | No | `qwen-plus` | Qwen model name |
| `QWEN_BASE_URL` | No | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Qwen-compatible endpoint |
| `DEMO_EMAIL` | No | `demo@healthos.pk` | Demo account email |
| `DEMO_PASSWORD` | No | — | Leave empty to skip demo seeding |
| `SEED_DEMO_DATA` | No | `true` | Set `false` to disable demo seeding |

### Frontend (`frontend/.env.local` or build-time env)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `VITE_API_BASE_URL` | No | `/api/v1` | Backend API URL; must be set at **build time** for production |

## Deployment

### Frontend (Vercel)

1. Push the repo to GitHub.
2. Create a new Vercel project and set **Root Directory** to `frontend`.
3. Framework preset: **Vite**.
4. Add the build-time environment variable:
   - `VITE_API_BASE_URL` = `https://<your-backend-host>/api/v1`
5. Deploy.
6. Verify direct navigation to `/dashboard`, `/lab-reports`, `/assistant`, `/plan`, and `/timeline` works by hard-refreshing those URLs.

### Backend (Railway / Render / Fly)

1. Push the repo to GitHub.
2. Create a new project and set **Root Directory** to `backend`.
3. The platform should detect `requirements.txt` and `Procfile`.
4. Set environment variables:
   - `SECRET_KEY` — freshly generated
   - `ENVIRONMENT` = `production`
   - `CORS_ORIGINS` = `https://<your-frontend-host>`
   - `AI_PROVIDER` = `mock`
   - `SEED_DEMO_DATA` = `false`
5. Optional but recommended: provision Postgres and set `DATABASE_URL`.
6. Set the platform health-check path to `/health`.
7. Deploy.

**Note:** After deploying the frontend, copy its real domain into the backend `CORS_ORIGINS` and redeploy the backend.

## Build Verification

```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
python -m compileall app
python -m pytest -q
```

## Health Checks

- `GET /` — returns API status
- `GET /health` — returns `{"status": "healthy"}` (recommended for platform health checks)
- `GET /api/v1/health` — returns richer diagnostic info

## Deployment Limitations

1. **SQLite on ephemeral filesystems is wiped on every restart/redeploy.** For real persistence, provision a PostgreSQL database and set `DATABASE_URL`.
2. **No migration tooling.** The schema is created via `Base.metadata.create_all()` on startup. Schema changes require manual intervention.
3. **Demo seeding runs on every startup.** Keep `SEED_DEMO_DATA` idempotent or set it to `false` in production.
4. **Original PDF uploads are not persisted.** Only the extracted text is stored in the database. The app will not crash on a read-only filesystem, but original files cannot be re-downloaded or re-parsed.
5. **Auth tokens are stored in `localStorage`.** This is a pre-existing design choice and remains XSS-readable.

## Security Notes

- `.env` files are gitignored. Never commit secrets.
- `SECRET_KEY` must be set in production; the app refuses to start without it.
- Wildcard (`*`) CORS origins are rejected in `ENVIRONMENT=production`.
- No demo credentials are included in source code; demo seeding is optional and controlled by environment variables.
