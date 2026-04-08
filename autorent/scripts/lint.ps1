$ErrorActionPreference = "Stop"

python -m ruff check app
python -m black --check app
python -m isort --check-only app
