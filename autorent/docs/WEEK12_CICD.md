# 12-апта: CI/CD баптау

Орындалды:

- GitHub Actions workflow қосылды:
  - `.github/workflows/ci.yml`
- Backend үшін автоматты тексерулер:
  - `ruff check .`
  - `pytest tests`
- Frontend үшін автоматты тексеру:
  - `npm run build`

Pipeline не істейді:

1. Репозиторийді checkout жасайды.
2. Python 3.12 орнатады және backend тәуелділіктерін жүктейді.
3. Backend lint пен тесттерді іске қосады.
4. Node.js 20 орнатады және frontend build жасайды.

Нәтиже:

- Pull request немесе push болғанда жоба автоматты тексеріледі.
- Қате код main/develop тармағына байқамай өтіп кету қаупі азайды.

Келесі қадам:

- 13-аптада load testing үшін `k6` сценарийлері қосылады.
- 14-аптада deploy және monitoring job-тары осы pipeline-ға жалғанады.
