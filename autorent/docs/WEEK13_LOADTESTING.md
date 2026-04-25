# Week 13: Load Testing

## Implemented

- `loadtests/smoke.js` checks `/healthz`, `/cars/`, and `/metrics`.
- `loadtests/auth-and-listing.js` exercises fleet browsing and invalid auth rejection.
- `Delivery` workflow runs the smoke suite automatically on `main/master` pushes and on manual dispatch.

## Run locally

1. Start the stack:
   `docker compose up --build`
2. Run the smoke suite:
   `docker run --rm --add-host=host.docker.internal:host-gateway -e BASE_URL=http://host.docker.internal:8000 -v "${PWD}/loadtests:/scripts" grafana/k6 run /scripts/smoke.js`
3. Run the extended suite:
   `docker run --rm --add-host=host.docker.internal:host-gateway -e BASE_URL=http://host.docker.internal:8000 -v "${PWD}/loadtests:/scripts" grafana/k6 run /scripts/auth-and-listing.js`

## Success criteria

- `http_req_failed < 5%` for the smoke suite.
- `p(95) < 800ms` for smoke browsing.
- `p(95) < 1200ms` for the extended browse/auth scenario.
