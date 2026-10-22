# Changelog

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
