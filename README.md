# ELD Trip Planner

Enter a trip (current location, pickup, drop-off, cycle hours used) and get a route map with required stops plus drawn FMCSA daily log sheets.

- `backend/` — Django API (`POST /api/trip/`, `GET /api/health/`)
- `frontend/` — React + Vite + Tailwind UI

## Local setup

```bash
cd backend && uv sync && cp .env.example .env   # add ORS_API_KEY
uv run python manage.py runserver
```

```bash
cd frontend && npm install && cp .env.example .env
npm run dev
```

_Live link, assumptions and project structure: TODO (Phase 9)._
