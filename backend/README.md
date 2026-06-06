# PimpleTV TV Launcher — Backend

Scraper + JSON API for the Android TV app. Designed to run **dockerized on a Raspberry Pi (arm64)**.
Implements the contract in [`../docs/api/openapi.yaml`](../docs/api/openapi.yaml).

## Status

Phase 0 scaffold. Runs now in **mock mode** (`PTV_MOCK_MODE=true`) serving sample matches so the
TV app can integrate against the real contract. The crawler + scheduler land in Phase 1.

## Design notes for the Pi

- **No headless browser in the runtime image.** Metadata is in static HTML → `httpx` + `selectolax`.
  Playwright is recon/fallback only (`requirements-recon.txt`, `scripts/recon_capture.py`) and is **not**
  installed in the Docker image.
- `python:3.11-slim` is multi-arch, so the same `Dockerfile` builds natively on the Pi.
- Single-process in-memory store; fine for LAN load. Redis can back it later if needed.

## Deploy to the Raspberry Pi (live)

Deployed at **`pi@192.168.0.56`**, running in live mode on **port 8090** (8000 is taken by
Portainer), container `pimpletv-api`, `restart: unless-stopped` (survives reboot).

One command from this machine (rsync source → rebuild on the Pi → health check):

```bash
cd backend
./deploy-pi.sh
```

Manually on the Pi:

```bash
cd ~/pimpletv-backend
docker compose -f docker-compose.pi.yml up -d --build
curl http://localhost:8090/api/health
```

Reachable on the LAN at **http://pimpletv.pi/** (Pi-hole DNS `pimpletv.pi → 192.168.0.57`
+ a Caddy reverse proxy → backend:8090), or directly at `http://192.168.0.57:8090/`.
The TV app uses the port-free `http://pimpletv.pi/` in release builds and the direct
`http://192.168.0.57:8090/` in debug builds (the emulator can't resolve `.pi` / route via Caddy).

Cross-build the image elsewhere: `docker buildx build --platform linux/arm64 -t pimpletv-api:arm64 .`

## Run locally (dev)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000/docs   (interactive)  ·  /api/matches  ·  /api/health
```

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/matches?sport=&window=` | list (summaries; no streams) |
| GET | `/api/matches/{id}` | full detail incl. `streams[]` |
| GET | `/api/health` | crawl freshness, match counts |

Errors use `{"error": {"code", "message"}}`.

## Config (env, `PTV_` prefix — see `.env.example`)

`PTV_MOCK_MODE`, `PTV_BASE_URL`, `PTV_LISTING_REFRESH_SECONDS`, `PTV_STREAM_WINDOW_MINUTES`,
`PTV_STREAM_REFRESH_SECONDS`, `PTV_TIMEZONE`, `PTV_PORT`.

## Layout

```
app/
  main.py        FastAPI app + lifespan (scheduler wires in here at Phase 1)
  routes.py      /api endpoints
  models.py      Pydantic contract models (T1.1)
  store.py       in-memory match store (T1.3)
  config.py      env-driven settings
  sample_data.py mock-mode seed data
scripts/
  recon_capture.py   T0.1 live-window payload capture (Playwright, dev-only)
tests/fixtures/      recon HTML/JSON captures
```

## Recon (T0.1 — live window only)

```bash
pip install -r requirements-recon.txt && playwright install chromium
python scripts/recon_capture.py 69175      # run within ~1h of kickoff
```
See [`../docs/recon-findings.md`](../docs/recon-findings.md).
