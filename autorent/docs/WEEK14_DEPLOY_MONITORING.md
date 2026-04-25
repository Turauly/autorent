# Week 14: Deploy and Monitoring

## Implemented

- `render.yaml` provisions a Render backend service, static frontend, and PostgreSQL database.
- `/healthz` and `/metrics` endpoints were added to the FastAPI backend.
- `docker-compose.yml` now includes `prometheus` and `grafana`.
- Grafana provisioning auto-loads a default `AutoRent Overview` dashboard.
- `delivery.yml` triggers Render deploy hooks after the smoke load test passes.

## Required GitHub secrets

- `RENDER_API_DEPLOY_HOOK`
- `RENDER_FRONTEND_DEPLOY_HOOK`

## Local monitoring stack

1. Start all services:
   `docker compose up --build`
2. Open Prometheus:
   `http://127.0.0.1:9090`
3. Open Grafana:
   `http://127.0.0.1:3000`
4. Login with:
   `admin / admin`

## Render deploy notes

- Backend health check path: `/healthz`
- Backend metrics path: `/metrics`
- Frontend must point `VITE_API_URL` to the deployed backend URL
- Update the default Render service URLs in `render.yaml` if you rename services
