$ErrorActionPreference = "Stop"

python -m black app
python -m isort app
python -m ruff check app --fix
