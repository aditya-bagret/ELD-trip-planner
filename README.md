# ELD Trip Planner

A trip planner for property-carrying truck drivers. Enter your current location, pickup, drop-off and the hours already used in your 70-hour/8-day cycle. The app routes the trip and simulates it minute by minute under the FMCSA Hours-of-Service rules. It schedules every required fuel stop, 30-min break, 10-hour rest and 34-hour restart, shows them on a map, and draws a filled-in paper-style daily log sheet for each day of the trip. It's built with a Django API and a mobile-first React UI.

**Live app:** https://YOUR-APP.vercel.app · **API:** https://YOUR-API.onrender.com/api/health/

> The API runs on Render's free tier and sleeps when idle, so the first request can take up to a minute.

![Screenshot](docs/screenshot.png)
<!-- TODO: add screenshot -->

## Features

- Four inputs: current location, pickup, drop-off, current cycle used (hrs).
- Full-screen route map (Leaflet + OpenStreetMap) with markers for pickup, drop-off, fuel stops, breaks, rests and restarts. Each marker shows its location, arrival time and duration.
- Trip summary (miles, driving time, total time, arrival) and a time-ordered stops list. Tapping a stop focuses it on the map.
- One FMCSA daily log sheet per day, drawn as SVG: header, 24-hour grid with the duty-status line, per-row totals (always 24.00 h), remarks at every status change, shipping documents and a 70 h/8 day recap.
- Map-first, app-like UI: bottom sheet on phones, side panel on desktop, 48 px touch targets.

## HOS rules and assumptions

Rules enforced: 11 h driving and a 14 h window per shift, a 30-min break after 8 h of driving, a 10 h rest to reset the shift, a 70 h/8-day cycle with a 34 h restart, fuel every 1,000 miles, and 1 h on duty each for pickup and drop-off.

Assumptions (all values in `backend/trips/constants.py`):

- The trip starts at 08:00 today; Day 1 before that is off duty.
- A 15-min pre-trip inspection starts every shift and a 15-min post-trip ends every shift (both on duty).
- Pickup and drop-off are 1 h on duty each. Fuel stops are 30 min on duty.
- A 30-min break (off duty) comes after 8 h of driving. A fuel stop, pickup or drop-off of 30+ min also counts as the break.
- 10-hour rests are logged on the Sleeper Berth line. 34-hour restarts are logged as Off Duty and taken when the 70 h cycle runs out.
- One home-terminal clock: no time zones, and each log day runs midnight to midnight.
- Driving speed per leg = route distance ÷ route duration from the routing service.
- "Current cycle used" counts as hours already in the 8-day window, with no per-day history, so nothing rolls off during the trip.
- Out of scope: split sleeper berth, adverse conditions, the 60 h/7-day cycle, short-haul exceptions.

## Tech stack

- **Backend:** Python 3.12, Django 5.2 (plain views, no database), django-cors-headers, gunicorn, managed with [uv](https://docs.astral.sh/uv/)
- **Frontend:** React 18 + Vite (JavaScript), Tailwind CSS v4, react-leaflet
- **APIs:** [OpenRouteService](https://openrouteservice.org/) for geocoding, HGV routing and reverse geocoding (free key)
- **Hosting:** Render (API), Vercel (UI)

## Local setup

You need Python 3.12 with uv, Node 18+, and a free OpenRouteService API key.

```bash
cd backend
cp .env.example .env          # set ORS_API_KEY
uv sync
uv run python manage.py runserver        # http://localhost:8000
uv run python manage.py test trips       # HOS engine tests
```

```bash
cd frontend
cp .env.example .env          # VITE_API_URL=http://localhost:8000
npm install
npm run dev                   # http://localhost:5173
```

## Project structure

```
backend/
  config/            settings (all from env), urls, wsgi
  trips/
    views.py         POST /api/trip/ (validation + orchestration), GET /api/health/
    geo.py           OpenRouteService client: geocode, route, reverse geocode
    hos.py           pure HOS simulation engine (no I/O)
    logs.py          pure: events -> daily sheets, totals, recap, remarks, map stops
    constants.py     every HOS number and assumption
    tests.py         engine + log tests
frontend/src/
  App.jsx            map-first layout and app state
  api.js             all fetch calls
  components/        TripForm, TripSummary, RouteMap, StopsList, LogsView, LogSheet, Assumptions
specs/               PRD, tech spec, HOS engine spec, design, implementation plan
```

## How the engine works

- **Route:** the three places are geocoded, then ORS returns two legs (current → pickup → drop-off) with miles, hours and geometry. Each leg's average speed comes from its distance ÷ duration.
- **Simulate:** `hos.simulate()` steps through the trip in integer minutes and keeps the shift, break, cycle and fuel counters. Before each driving chunk it checks the limits in a fixed order (cycle → 11 h/14 h → 8 h break → fuel). Each chunk runs until the next limit or the end of the leg.
- **Stops:** when a limit is hit it inserts the right event (34 h restart, post-trip + 10 h rest + pre-trip, 30-min break, or 30-min fuel stop), placed on the route by interpolating the geometry. Positions are reverse-geocoded to "City, ST".
- **Daily logs:** `logs.build_daily_logs()` splits the event list at every midnight. For each day it builds the duty-status segments, per-status totals (rounded so they always sum to exactly 24.00 h), miles, remarks and the 70 h/8-day recap.
- **Draw:** the API returns one JSON payload (route, stops, sheets). The UI draws the map and renders each sheet as an SVG copy of the paper log.
