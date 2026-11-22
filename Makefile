.PHONY: setup run serve smoke models api-check clean

# A bare `make` runs the smoke test, as it did before the uniform targets were added.
.DEFAULT_GOAL := smoke

# Uniform targets for The Playbooks. The book's commands (pip install -r requirements.txt,
# python download_models.py, python test_pipeline.py, docker-compose up -d,
# uvicorn src.api.main:app --reload) still work as printed.

# Install the locked dependencies and download the two encoder models into models/.
setup: models

# Encode the sample image, review and video on CPU and print the vectors (Steps 4-5). No Docker.
run: setup lfs-sample
	uv run --frozen python test_pipeline.py

# Start PostgreSQL and Milvus in Docker, then the API on http://localhost:8000 (Steps 6-7).
serve: setup
	docker compose up -d --wait
	uv run --frozen uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Encoder playbook on CPU (Steps 4-5), no Docker. Downloads the models on first run.
smoke: models
	uv run --frozen pytest -q tests/test_smoke.py

models:
	uv sync --frozen
	uv run --frozen python download_models.py

# Full stack (Steps 6-7). Start the services first: docker compose up -d --wait
api-check: models
	uv run --frozen bash tests/api_check.sh

# The one video `make run` encodes, if the clone skipped Git LFS files.
.PHONY: lfs-sample
lfs-sample:
	@if head -c 100 sample_data/product_videos/white_sneakers.mp4 | grep -q git-lfs; then \
		git lfs install --local && git lfs pull --include="sample_data/product_videos/white_sneakers.mp4"; fi

# Stop the Docker services and delete their volumes, and remove test caches.
# Downloaded models and the sample data are kept.
clean:
	-docker compose down -v --remove-orphans
	rm -rf .pytest_cache
