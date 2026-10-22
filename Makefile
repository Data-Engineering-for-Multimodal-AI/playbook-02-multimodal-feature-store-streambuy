.PHONY: smoke models api-check

# Encoder playbook on CPU (Steps 4-5), no Docker. Downloads the models on first run.
smoke: models
	uv run --frozen pytest -q tests/test_smoke.py

models:
	uv sync --frozen
	uv run --frozen python download_models.py

# Full stack (Steps 6-7). Start the services first: docker compose up -d --wait
api-check: models
	PYTHON=".venv/bin/python" bash tests/api_check.sh
