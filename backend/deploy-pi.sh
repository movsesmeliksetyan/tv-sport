#!/usr/bin/env bash
# Deploy the backend to the Raspberry Pi: rsync the source, then rebuild + restart
# the container in live mode (port 8090). Idempotent — run again to update.
#
# Usage:  ./deploy-pi.sh
# Override the target if needed:  PI_HOST=pi@192.168.0.56 PI_DIR=~/pimpletv-backend ./deploy-pi.sh
set -euo pipefail

PI_HOST="${PI_HOST:-pi@192.168.0.56}"
PI_DIR="${PI_DIR:-pimpletv-backend}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "==> Syncing source to ${PI_HOST}:${PI_DIR}"
rsync -az --delete \
  --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.pytest_cache' \
  "${HERE}/" "${PI_HOST}:${PI_DIR}/"

echo "==> Building + starting container (live mode, :8090)"
ssh "${PI_HOST}" "cd ${PI_DIR} && docker compose -f docker-compose.pi.yml up -d --build"

echo "==> Health check"
ssh "${PI_HOST}" "sleep 6 && curl -s http://localhost:8090/api/health" && echo
echo "==> Done. Reachable on the LAN at http://pimpletv.pi:8090/ (and http://192.168.0.57:8090/)"
