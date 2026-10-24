# StreamBuy Multimodal Feature Store

**Chapter 2 playbook** from *Data Engineering for Multimodal AI* (O'Reilly, 2026). Page numbers to be confirmed.
Book: https://oreil.ly/data-engineering-multimodal

> Want the code exactly as printed? Use the `first-edition` tag. This branch is the 2026 maintenance update; see [Differences from the printed book](#differences-from-the-printed-book).

## What you'll build

A multimodal feature store for the fictional StreamBuy e-commerce platform. It ingests product images, customer review text and product video clips, encodes each modality into dense vectors, stores them in PostgreSQL (metadata and results) and Milvus (vectors), and exposes a FastAPI service for similarity search.

```
┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│ Product Data │────▶│   Encoders   │────▶│   Storage   │
│  images/     │     │  ResNet18    │     │  PostgreSQL │
│  reviews/    │     │  MiniLM-L6   │     │  Milvus     │
│  videos/     │     │  ResNet18    │     └──────┬──────┘
└──────────────┘     └──────────────┘            │
                                                 ▼
                                          ┌─────────────┐
                                          │  FastAPI     │
                                          │  /search/    │
                                          │  /products/  │
                                          └─────────────┘
```

| Modality | Model               | Output Dim | Notes                                    |
|----------|---------------------|------------|------------------------------------------|
| Image    | ResNet18 (ImageNet) | 512        | Classification head removed              |
| Text     | all-MiniLM-L6-v2    | 384        | Sentence-level semantic embedding        |
| Video    | ResNet18 (ImageNet) | 512        | 8 uniformly sampled frames, averaged     |

All encoders normalize output vectors to unit length, so a dot product is the cosine similarity.

Steps 1–5 run the encoders on your laptop CPU with no other services. Steps 6–8 are optional and need Docker.

## Quick start

You need Python 3.12 or newer, [Git LFS](https://git-lfs.com) (for the sample videos), and Docker only for Steps 6–8. Plan for about 4 GB of disk space.

### Step 1: Clone the repository

The sample videos are stored with Git LFS. A full clone downloads all 31 videos (842 MB):

```bash
git lfs install
git clone https://github.com/Data-Engineering-for-Multimodal-AI/playbook-02-multimodal-feature-store-streambuy.git
cd playbook-02-multimodal-feature-store-streambuy
```

The tests use only one video. For a light clone (about 42 MB) that fetches just that one:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Data-Engineering-for-Multimodal-AI/playbook-02-multimodal-feature-store-streambuy.git
cd playbook-02-multimodal-feature-store-streambuy
git lfs pull --include="sample_data/product_videos/white_sneakers.mp4"
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### Step 3: Install dependencies (as printed)

```bash
pip install -r requirements.txt
```

The versions are pinned. On Linux, PyTorch comes from its CPU-only index, which `requirements.txt` adds.

Using [uv](https://docs.astral.sh/uv/) instead: `uv sync`, then prefix the Python commands below with `uv run`.

### Step 4: Download the pretrained models (one time)

```bash
python download_models.py
```

| Model              | Size    | Used By                 |
|--------------------|---------|-------------------------|
| ResNet18           | ~45 MB  | Image and video encoder |
| all-MiniLM-L6-v2   | ~87 MB  | Text/review encoder     |

### Step 5: Run the encoder tests (no Docker)

```bash
python test_pipeline.py
```

All five tests should print `[PASS]`. See [Expected output](#expected-output).

### Step 6: Start the full stack (optional, needs Docker)

```bash
docker-compose up -d            # or: docker compose up -d --wait
```

| Service    | Port  | Purpose                           |
|------------|-------|-----------------------------------|
| PostgreSQL | 5432  | Product metadata and job tracking |
| Milvus     | 19530 | Vector similarity search          |
| etcd       | 2379  | Milvus metadata store (internal)  |
| MinIO      | 9000  | Milvus object storage             |

Wait until all services are healthy (about 30–60 seconds; `docker compose ps` shows the status), then start the API:

```bash
uvicorn src.api.main:app --reload
```

If another PostgreSQL already uses port 5432 on your machine, the API connects to that one instead and fails with `role "user" does not exist`. Start the stack with `POSTGRES_PORT=5433 docker compose up -d` and run the API with `DATABASE_URL=postgresql://user:password@localhost:5433/streambuy_features`. All settings are listed in [`.env.example`](.env.example).

### Step 7: Try the API

**Ingest a product:**

```bash
curl -X POST http://localhost:8000/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blue Yellow Sneakers",
    "category": "footwear",
    "brand": "StreamBuy",
    "price": 89.99,
    "data_paths": {
      "image": "sample_data/product_images/blue_yellow_sneakers.jpg",
      "review": "sample_data/reviews/blue_yellow_sneakers_reviews.txt"
    }
  }'
```

**Check job status:**

```bash
curl http://localhost:8000/jobs/1
```

**Get product features:**

```bash
curl http://localhost:8000/products/1/features
```

**Search for similar products:**

```bash
curl -X POST "http://localhost:8000/search/image?limit=5" \
  -H "Content-Type: application/json" \
  -d '{"query_vector": [0.01, -0.02, ...]}'
```

(Use a real 512-dimensional vector from the encoder output. `tests/api_check.sh` shows one way to build it.)

The interactive API docs are at http://localhost:8000/docs.

### Step 8: Shut down

```bash
docker-compose down             # add -v to also delete the stored data
deactivate                      # exit the virtual environment
```

### Checks

- `make smoke`: Steps 4–5 plus checks of the similarity claims below (about 1 minute after the first model download).
- `make api-check`: Steps 6–7 with the services running. Runs the curl calls above, restarts the API and checks that the stored vectors and job status survive.

## Tested on

| Date | OS | Python | Key libraries |
|---|---|---|---|
| 2026-10-22 | macOS 26.5.1 (arm64), Docker 28.0.1 | 3.12.15, 3.13.16 | torch 2.14.1, torchvision 0.29.1, sentence-transformers 6.2.0, fastapi 0.161.0, starlette 1.9.0, pymilvus 3.0.2, asyncpg 0.32.0, opencv-python 5.0.0, numpy 2.5.4; Milvus 3.0.3, PostgreSQL 16 |
| CI, on every push | ubuntu-latest | 3.12, 3.13 | same, from `uv.lock` (encoders); full stack with Docker on 3.12 |

## Differences from the printed book

| What | Printed version | Now | Why |
|---|---|---|---|
| Starting the API (Step 6) | `uvicorn` exited with `ConnectionNotExistException: should create connection first` | Starts | Collections were created before the Milvus connection; now after it |
| Search request (Step 7) | `{"query_vector": [...]}` returned HTTP 422 | Works as printed | The endpoint expected a bare JSON array |
| API restart | Deleted all vectors; job status lost; unknown jobs returned HTTP 200 | Vectors and job status kept; unknown jobs return 404 | Collections were dropped on every start; job status was only in memory |
| Docker images | Milvus v2.4.0, etcd v3.5.5, `minio/minio:RELEASE.2023-03-20` | Milvus v3.0.3, etcd v3.5.25, `milvusdb/minio:RELEASE.2024-12-18`, as in Milvus's own compose file | MinIO stopped publishing Docker images in October 2025; current Milvus |
| Connection settings | Hard-coded | `DATABASE_URL`, `MILVUS_HOST`, `MILVUS_PORT`, `POSTGRES_PORT` (same defaults) | A local PostgreSQL on 5432 took the place of the Docker one |
| Clone (Step 1) | `git clone <repo-url>` / `cd streambuy-featurestore`; no mention of Git LFS | Real URL and folder; Git LFS, with a light option | Without Git LFS the video test failed |
| Install | Python 3.10+, unpinned; `pymilvus>=2.5.0` | Python 3.12+, pinned; `pymilvus<3.1` | pymilvus 3.1 removes the API this code uses |
| Sample images | 20 files, including a portrait photo | 19 product photos | The portrait was unused and showed an identifiable person |
| `download_models.py` output | | No `HTTP Request:` log lines | Matches the expected output |

The full list is in [CHANGELOG.md](CHANGELOG.md).

## Data and licenses

| Data | Source | License |
|---|---|---|
| `sample_data/product_images/` (19 photos) | Unsplash and Pexels; per-file sources weren't recorded | [Unsplash License](https://unsplash.com/license) / [Pexels License](https://www.pexels.com/license/) |
| `sample_data/product_videos/` (31 clips, Git LFS) | Pexels Videos; per-file sources weren't recorded | [Pexels License](https://www.pexels.com/license/) |
| `sample_data/reviews/` (18 texts) | Written synthetically for this playbook | MIT, like the code |
| ResNet18 weights (downloaded) | torchvision, ImageNet-trained | [BSD-3-Clause (torchvision)](https://github.com/pytorch/vision/blob/main/LICENSE) |
| all-MiniLM-L6-v2 (downloaded) | [Hugging Face](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Apache 2.0 |

Details and caveats are in [`sample_data/README.md`](sample_data/README.md). The products differ across modalities on purpose: a "white sneakers" image and video may show different shoes.

## Expected output

From my run on 2026-10-22: macOS 26.5.1 (arm64), Python 3.12.15, a light clone from GitHub, `pip install -r requirements.txt` (88 s). Python 3.13.16 gave the same numbers.

`python download_models.py` (84 s on the first run). On macOS, PyTorch also prints a `NOTE: Redirects are currently not supported in MacOs.` line, and Hugging Face may print a warning about unauthenticated requests; both are harmless.

```
============================================================
StreamBuy Feature Store — Model Setup
============================================================

Model directory: /path/to/playbook-02-multimodal-feature-store-streambuy/models

[1/2] ResNet18 (image & video encoder)
  Downloading ResNet18 pretrained weights...
  Saved ResNet18 to /path/to/playbook-02-multimodal-feature-store-streambuy/models/resnet18.pth (44.7 MB)

[2/2] all-MiniLM-L6-v2 (text/review encoder)
  Downloading all-MiniLM-L6-v2 sentence transformer...
  Saved all-MiniLM-L6-v2 to /path/to/playbook-02-multimodal-feature-store-streambuy/models/all-MiniLM-L6-v2 (87.3 MB)

============================================================
Setup complete. All models saved locally.
The pipeline will now run fully offline.
============================================================
```

`python test_pipeline.py` (59 s). Lines are prefixed with the logger name (`INFO:__main__:`, `INFO:src.encoders.image:` and so on); this excerpt shows the test lines without the prefix:

```
--- Test 1: Image Encoder ---
[PASS] Image encoder: shape=(512,), norm=1.000000

--- Test 2: Text Encoder ---
[PASS] Text encoder: shape=(384,), norm=1.000000

--- Test 3: Video Encoder ---
[PASS] Video encoder: shape=(512,), norm=1.000000

--- Test 4: Cross-Modal Similarity ---
  Same category (sneakers img↔vid): 0.7042
  Diff category (sneakers↔headphones): 0.5811
[PASS] Cross-modal similarity computed successfully

--- Test 5: Batch Encoding ---
  Encoded blue_yellow_sneakers.jpg
  ...
  Encoded white_sneakers.jpg
[PASS] Batch encoding: 19 images encoded

  Similarity matrix (first 5 products):
            blue_yel  blue_yel  brown_le  cream_sn  faux_lea
  blue_yello    1.0000    0.8685    0.6285    0.7048    0.6611
  blue_yello    0.8685    1.0000    0.6053    0.7230    0.6066
  brown_leat    0.6285    0.6053    1.0000    0.6653    0.7159
  cream_snea    0.7048    0.7230    0.6653    1.0000    0.6041
  faux_leath    0.6611    0.6066    0.7159    0.6041    1.0000

ALL TESTS PASSED
```

What to look for: image and video vectors are 512-dimensional and text vectors 384-dimensional, all with norm 1.000000. Two views of the same blue/yellow sneakers score 0.87, higher than sneakers vs boots (0.63). Across all 19 images, the closest match to `blue_yellow_sneakers` is a different pair of blue sneakers (0.871), just above its second view (0.869): an ImageNet model captures how things look, not which product they are.

`uvicorn src.api.main:app` (Step 6) on first start. pymilvus 3.0 also prints `PyMilvusDeprecationWarning` lines, because the code uses the ORM API that pymilvus 3.1 removes; they don't affect the playbook.

```
INFO:     Started server process [46728]
INFO:     Waiting for application startup.
INFO:src.db.postgres:Connected to PostgreSQL database
INFO:src.db.milvus:Connected to Milvus server
INFO:src.db.milvus:Created collection: streambuy_image_features (dim=512)
INFO:src.db.milvus:Created collection: streambuy_video_features (dim=512)
INFO:src.db.milvus:Created collection: streambuy_review_features (dim=384)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Step 7 responses (from `tests/api_check.sh`, which runs the same calls; timestamps shortened):

```
POST /products/ -> {"job_id":"1","product_id":"1","modalities":["image","review"],"status":"pending",...}
GET /jobs/1 -> {"status":"success","job_id":1,"modalities_processed":2}
GET /products/1/features -> 2 results
POST /search/image -> [{"product_id":1,"distance":0.0}]
GET /jobs/999999 -> HTTP 404
API restarted
GET /jobs/1 -> {"status":"processed","job_id":1}
POST /search/image -> [{"product_id":1,"distance":0.0}]
API CHECK PASSED
```

The search used the image's own vector, so the product finds itself at distance 0.0. After a restart, `/jobs/1` reports the status stored in PostgreSQL (`processed`).

## Extending the code

After completing the playbook, here are some exercises to deepen your
understanding:

1. **Add a new modality** — Create an audio encoder (e.g., using a
   pretrained audio model) and register it in the `EncoderFactory`.
2. **Implement hybrid search** — Combine vector similarity with metadata
   filters (e.g., category or price range) in the `/search/` endpoint.
3. **Add batch ingestion** — Create a new endpoint that accepts multiple
   products in a single request and processes them concurrently.
4. **Export embeddings** — Write a utility that exports all stored embeddings
   to Parquet files for offline analysis in pandas or Spark.
5. **Add a simple UI** — Build a Streamlit or Gradio front-end that lets
   you upload an image and see visually similar products.

A note for production use: the encoders run inside the API's event loop, so the API is unresponsive while a product is being encoded, and the CORS settings allow any origin. Both are fine for this local playbook.

## Project structure

```
playbook-02-multimodal-feature-store-streambuy/
├── README.md                   # This file — playbook and architecture
├── CHANGELOG.md                # Changes since the printed book
├── requirements.txt            # Pinned dependencies (exported from uv.lock)
├── pyproject.toml, uv.lock     # Same dependencies for uv
├── download_models.py          # One-time model setup script
├── test_pipeline.py            # Encoder pipeline tests (no Docker needed)
├── docker-compose.yml          # PostgreSQL + Milvus infrastructure
├── schema.sql                  # Database schema
├── .env.example                # Connection settings (environment variables)
├── Makefile                    # make smoke, make api-check
├── models/                     # Pretrained weights (created by download_models.py)
├── src/
│   ├── api/main.py             # FastAPI endpoints
│   ├── db/
│   │   ├── postgres.py         # PostgreSQL client (asyncpg)
│   │   └── milvus.py           # Milvus vector store client
│   ├── encoders/
│   │   ├── factory.py          # Encoder factory (modality → encoder)
│   │   ├── image.py            # ResNet18 image encoder (512-dim)
│   │   ├── text.py             # MiniLM-L6 text encoder (384-dim)
│   │   └── video.py            # Frame-sampled video encoder (512-dim)
│   ├── models/pipeline.py      # Pydantic data models
│   └── worker/
│       ├── tasks.py            # Encoding task processor
│       └── manager.py          # Async task manager
├── tests/
│   ├── test_smoke.py           # make smoke
│   └── api_check.sh            # make api-check (full stack)
└── sample_data/
    ├── README.md               # Sources, licenses and notes
    ├── product_images/         # 19 product photos
    ├── product_videos/         # 31 product video clips (Git LFS)
    └── reviews/                # 18 customer review text files
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `... is a Git LFS pointer, not a video` | Install Git LFS and run `git lfs pull --include="sample_data/product_videos/white_sneakers.mp4"` (or `git lfs pull` for all videos) |
| `Run 'python download_models.py' first` | Step 4 hasn't been run in this folder |
| `ImportError: ... libtorch_cpu.dylib` | Your PyTorch install is corrupted or was built for a different environment. Create a fresh virtual environment and reinstall: `pip install -r requirements.txt` |
| `AssertionError: Sample image not found` | Run the commands from the repository root |
| `role "user" does not exist` | Another PostgreSQL is using port 5432; see the note in Step 6 |
| `docker-compose up` fails | Make sure Docker is running and ports 5432, 19530, 9000 and 9001 are free |
| `Connection refused` on API calls | Wait until all Docker services are healthy before starting uvicorn |

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2025-2026 Data Engineering for Multimodal AI. The sample images and videos are under their own licenses; see [Data and licenses](#data-and-licenses).
