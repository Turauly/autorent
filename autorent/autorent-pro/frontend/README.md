# AutoRent Frontend

## Run

1. `npm install`
2. `npm run dev`

App runs on `http://127.0.0.1:5173`.

By default API URL is `http://127.0.0.1:8000`.
If needed, create `.env` from `.env.example`.

## Role UI

- `admin` -> `/admin` panel (car add/delete)
- `user` -> `/client` page (car browsing)
- Registration flow uses email code:
  1) request code
  2) confirm with code + password
