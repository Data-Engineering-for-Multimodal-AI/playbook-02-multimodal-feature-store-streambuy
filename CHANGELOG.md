# Changelog

## Unreleased (v1.1.0)

Nothing the book shows has changed.

### Added
- `make load-samples` adds the 19 sample products through `POST /products/`, and `make search IMAGE=...` or
  `make search TEXT=...` searches them by photo or by text (`scripts/`).
- `make setup`, `make run`, `make serve` and `make clean`. `make run` encodes the sample image,
  review and video on CPU (Steps 4-5); `make serve` starts the Docker services and the API
  (Steps 6-7). `make smoke` and `make models` are unchanged.
- `.devcontainer/` so the repo opens in GitHub Codespaces, with Docker-in-Docker for the services.
  Git LFS files are not pulled automatically; `make run` fetches the one video it needs.
- CI: a weekly scheduled run, a `make run` step, and a job that builds the devcontainer and runs
  `make run` inside it.

### Fixed
- `make api-check` used a hard-coded `.venv/bin/python`. It now runs through `uv run`.

### Changed
- README: a numbered "Run it" section; the book's steps are under "Run it the way the book does".
- README opening: a title that says what you'll do, three sentences on why, the example and what you'll do, then the data engineering problem and what you'll work with.
- Book page numbers now match the printed book (they were Early Release page numbers).

## 2026.10.1 (2026-10-27)

### Changed
- README, after checking against the book (Early Release, pages 60–68): page numbers; the
  differences table's left column is the first edition.

## 2026.10 (2026-10-22): 2026 maintenance update

The printed version is tagged `first-edition`.

### Fixed
- **The API starts.** `uvicorn src.api.main:app` exited with `ConnectionNotExistException: should create connection first`, because the Milvus collections were created at import time, before connecting. They are now created after connecting.
- **The printed search request works.** `POST /search/{modality}` with `{"query_vector": [...]}` returned HTTP 422; the endpoint expected a bare JSON array.
- **Restarting the API keeps the vectors.** Every start dropped the Milvus collections while PostgreSQL kept its results, so search returned nothing for stored products.
- **Job status survives a restart.** `/jobs/{id}` falls back to the status stored in PostgreSQL, and returns 404 for a job that doesn't exist (it returned 200 with "Job not found").
- A clone without Git LFS failed with "Could not read video frames"; the video encoder now says the file is an LFS pointer and how to fetch it.
- `download_models.py` no longer prints about 40 `HTTP Request:` log lines.
- README: the real clone URL and folder name, Python 3.12+, Git LFS instructions, and expected output from a real run.

### Changed
- **Docker services** follow Milvus's own v3.0.3 standalone compose file: Milvus v2.4.0 → v3.0.3, etcd v3.5.5 → v3.5.25, `minio/minio:RELEASE.2023-03-20` → `milvusdb/minio:RELEASE.2024-12-18` (MinIO stopped publishing Docker images in October 2025). PostgreSQL stays at 16.
- `DATABASE_URL`, `MILVUS_HOST` and `MILVUS_PORT` are read from the environment (defaults unchanged). `POSTGRES_PORT` changes the PostgreSQL host port in `docker-compose.yml`, for machines where 5432 is taken.
- `pymilvus` is pinned below 3.1, which removes the ORM API (`connections`, `Collection`, `utility`) this code uses.
- On Linux, `torch` and `torchvision` come from the PyTorch CPU index (no CUDA libraries).
- The README follows the standard playbook layout; the duplicated MIT text in the README is replaced by a link to `LICENSE`.

### Removed
- `sample_data/product_images/Serene Woman Portrait.png`: an unused photo of an identifiable person with no recorded source. The tests already skipped it.
- `python-dotenv` and `tqdm` from the requirements (never imported).

### Added
- `pyproject.toml`, `uv.lock`, and a pinned `requirements.txt` exported from the lock (Python 3.12+).
- `tests/test_smoke.py` (`make smoke`) and `tests/api_check.sh` (`make api-check`), which runs the README's API calls and restarts the API.
- GitHub Actions: encoder smoke test on Python 3.12 and 3.13, the printed `pip install` path, and a full-stack job with Docker.
- `.env.example`.
- Sources and licenses for the sample data in `sample_data/README.md`.
