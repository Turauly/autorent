# AutoRent: Автосалонда автокөліктерді жалға беруді есепке алу

Бұл жоба пәндік тақырыпқа сай автокөлікті жалға беру процесін есепке алу жүйесін құруға арналған.

## 1) Міндетті талаптар чек-лисі

Төмендегі талаптар жобаға міндетті түрде енгізіледі:

- [x] Пайдаланушы аутентификациясы: тіркелу, кіру, шығу
- [x] Рөлдер: `user` және `admin`
- [x] Тақырыптың негізгі функционалдығы (автокөлік, жалдау, қайтару, қолжетімділік)
- [x] Админ-панель (контент/анықтамалықтарды басқару)
- [x] Адаптивті интерфейс (desktop + mobile)
- [x] Дерекқормен интеграция
- [x] Frontend пен Backend арасында RESTful API
- [x] Клиенттік және серверлік валидация, error handling
- [x] Іздеу және сүзгілеу
- [x] Сұрыптау және пагинация
- [x] Логирование және мониторинг
- [x] Автоматтандырылған тесттер (unit + integration)
- [x] Қауіпсіздік: пароль хэштеу, CORS баптауы, SQLAlchemy ORM арқылы SQLi тәуекелін азайту, React auto-escaping
- [x] Cloud deploy (Render blueprint + deploy hook workflow)
- [x] Құжаттама: architecture, API docs, setup, user guide
- [x] Docker (`Dockerfile` + `docker-compose`)
- [x] CI/CD pipeline (GitHub Actions/GitLab CI)
- [x] Мониторинг стегі (Prometheus/Grafana)
- [x] Жүктемелік тест (k6)

## 2) 15 апталық roadmap және бағалау

1. 1-апта (5%): Жоспарлау
   Тақырып, мақсат, scope, команда рөлдері, архитектуралық жоспар.
   Бағалау: жоспардың толықтығы мен анықтығы.
2. 2-апта (5%): Ортаны баптау
   GitHub repo + README, project structure, code style, branching strategy.
   Бағалау: баптаудың дұрыстығы.
3. 3-апта (10%): Аутентификация/авторизация
   Register/Login/Logout, user/admin role.
   Бағалау: қауіпсіз және жұмыс істейтін auth.
4. 4-апта (10%): ДБ және модельдер
   DB schema, ORM entity/model.
   Бағалау: логикалық және оңтайлы құрылым.
5. 5-апта (10%): Негізгі функционал 1
   Базалық CRUD.
   Бағалау: тұрақтылық және дұрыстық.
6. 6-апта (10%): Негізгі функционал 2
   Кеңейтілген функциялар, API жауап сапасы.
   Бағалау: толық функционал.
7. 7-апта (5%): UI 1
   Негізгі интерфейс және адаптив.
   Бағалау: қолдану ыңғайлылығы.
8. 8-апта (5%): UI 2
   UI/UX жақсарту, іздеу/сүзгі, backend интеграция.
   Бағалау: интеграция сапасы.
9. 9-апта (5%): Админ-панель
   Әкімші басқару беттері.
   Бағалау: функционал және ыңғайлылық.
10. 10-апта (5%): Кеңейтілген мүмкіндіктер
    Сұрыптау, пагинация, валидация, error handling.
    Бағалау: сенімділік.
11. 11-апта (5%): Контейнеризация
    Dockerfile, docker-compose, backend + DB (+frontend).
    Бағалау: контейнерде іске қосылуы.
12. 12-апта (5%): CI/CD
    Build, test, deploy automation.
    Бағалау: жұмыс істейтін pipeline.
13. 13-апта (10%): Тестілеу және жүктеме
    Unit/integration + k6/JMeter.
    Бағалау: coverage және performance метрикалары.
14. 14-апта (10%): Deploy және мониторинг
    Cloud deploy + Prometheus/Grafana/ELK.
    Бағалау: тұрақты deploy және метрика қолжетімділігі.
15. 15-апта (10%): Финал
    Презентация және demo.
    Бағалау: толықтық, сапа, ұсынылу деңгейі.

## 3) Апталық есеп форматы

Әр аптада `docs/WEEKLY_REPORT_TEMPLATE.md` негізінде есеп тапсырылады:
- Орындалған тапсырмалар
- Ағымдағы прогресс (%)
- Қиындықтар және шешімдер
- Келесі апта жоспары

## 4) Техникалық бағыт

- Backend: FastAPI + SQLAlchemy + JWT
- DB: PostgreSQL
- Infra: Docker, CI/CD, Render, Prometheus, Grafana
- Tests: pytest + integration tests + k6
- Monitoring: Prometheus + Grafana

## Code Style және Branching

- Code style: `.editorconfig`, `pyproject.toml` (ruff/black/isort)
- Frontend formatting: `autorent-pro/frontend/.prettierrc`
- Branching: `docs/BRANCHING.md`
- Contributing: `docs/CONTRIBUTING.md`

## Quick Start (Backend)

1. Install deps: `pip install -r requirements.txt`
2. Start API: `python -m uvicorn app.main:app --reload`
3. Open docs: `http://127.0.0.1:8000/docs`

## Docker

- Run all services: `docker compose up --build`
- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3000` (`admin/admin`)

## CI/CD

- GitHub Actions workflow: `.github/workflows/ci.yml`
- Delivery workflow: `.github/workflows/delivery.yml`
- Backend pipeline:
  - install Python 3.12 dependencies
  - run `ruff check .`
  - run `pytest tests`
- Frontend pipeline:
  - install Node.js 20 dependencies with `npm ci`
  - run `npm run build`
- Delivery pipeline:
  - starts backend service
  - runs k6 smoke suite
  - triggers Render deploy hooks for backend/frontend if secrets are configured

## Migrations (Alembic)

- Upgrade to latest migration:
  `alembic upgrade head`
- Create a new migration:
  `alembic revision -m "describe_change"`

## Frontend (React)

- Path: `autorent-pro/frontend`
- Install: `npm install`
- Start: `npm run dev`
- URL: `http://127.0.0.1:5173`

## Monitoring

- Metrics endpoint: `http://127.0.0.1:8000/metrics`
- Health endpoint: `http://127.0.0.1:8000/healthz`
- Grafana dashboard provisioning: `monitoring/grafana/`
- Prometheus config: `monitoring/prometheus/prometheus.yml`

## Load Testing

- Smoke suite: `loadtests/smoke.js`
- Extended suite: `loadtests/auth-and-listing.js`

## Deploy

- Render blueprint: `render.yaml`
- Required GitHub secrets for auto-deploy:
  - `RENDER_API_DEPLOY_HOOK`
  - `RENDER_FRONTEND_DEPLOY_HOOK`
- One-time manual step:
  - confirm final Render service URLs and set `VITE_API_URL` if service names change

## Email Delivery

Set SMTP variables in `.env` to send real emails.
If SMTP is not configured, code is logged in backend logs (development only).

## Admin Helper

- Set single admin by email (DB must be running):
  `python tools/set_admin_by_email.py user@example.com`
