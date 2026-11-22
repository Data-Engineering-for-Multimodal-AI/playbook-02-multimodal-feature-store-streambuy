# Playbook 02: Search products by photo, review and video
**How to build a multimodal feature store with Milvus and PostgreSQL.** Chapter 2 of [*Data Engineering for Multimodal AI*](https://oreil.ly/data-engineering-multimodal) (O'Reilly, 2026), pages 61–69.

An online store has photos, reviews and videos for every product, but a search that reads only one of them misses what the others show. In this repo, we explore this with StreamBuy, a fictional social commerce platform. Follow along to turn each kind of product data into vectors, store them in Milvus and PostgreSQL, and search them through an API you can feed your own products.

**The problem.** Images, text and video each produce vectors of a different kind and size, and one system has to store all of them and search them quickly.

**What you'll work with.** You'll encode each modality with its own model, normalize the vectors so they can be compared, keep vectors in Milvus and product details in PostgreSQL, and process new products in the background.

> Following the book? Its Steps 1–8 are in [Run it the way the book does](#run-it-the-way-the-book-does) and still work as printed. Want the code exactly as printed? Use the `first-edition` tag. This branch is the 2026 maintenance update; see [Differences from the printed book](#differences-from-the-printed-book).

## Run it

You need [uv](https://docs.astral.sh/uv/), [Git LFS](https://git-lfs.com), `make`, and Docker for steps 3 to 6. Or open the repo in a GitHub Codespace, where all of them are ready. On Windows without `make`, use a Codespace or the book's steps below.

**1. Get the code.** This light clone is about 42 MB and fetches only the one video the tests use.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Data-Engineering-for-Multimodal-AI/playbook-02-multimodal-feature-store-streambuy.git
cd playbook-02-multimodal-feature-store-streambuy
```

**2. Encode the sample products.** Installs the locked dependencies, downloads the two encoder models (`python download_models.py`) and runs the five encoder tests (`python test_pipeline.py`). No Docker needed. On a fresh clone this took 1 min 51 s on a Mac, most of it the model download.

```bash
make run
```

You should see five `[PASS]` lines, then `ALL TESTS PASSED`:

```
[PASS] Image encoder: shape=(512,), norm=1.000000
[PASS] Text encoder: shape=(384,), norm=1.000000
[PASS] Video encoder: shape=(512,), norm=1.000000
[PASS] Cross-modal similarity computed successfully
[PASS] Batch encoding: 19 images encoded
```

Each photo, review and video is now a vector of length 1. Two photos of the same sneakers score 0.87 (1.0 means identical); sneakers and boots score 0.63.

**3. Start the feature store.** Starts PostgreSQL and Milvus in Docker (`docker compose up -d --wait`), then the API on port 8000 (`uvicorn src.api.main:app`). Leave it running.

```bash
make serve
```

You should see `Application startup complete.` If another PostgreSQL already uses port 5432 on your machine, first run `export POSTGRES_PORT=5433 DATABASE_URL=postgresql://user:password@localhost:5433/streambuy_features` in this terminal and the next one.

**4. Add the products.** In a second terminal. Sends each of the 19 sample products to `POST /products/` with its photo and reviews, the same request as the book's curl example. The API encodes them, stores the vectors in Milvus and the product details in PostgreSQL.

```bash
make load-samples
```

You should see one `success` line per product. This took 3 min 20 s on a Mac, because the API encodes one product at a time.

```
  success  blue yellow sneakers                 image + review
  ...
  success  white sneakers                       image + review
```

**5. Search.** By photo:

```bash
make search IMAGE=sample_data/product_images/white_sneakers.jpg
```

```
Closest image matches for 'sample_data/product_images/white_sneakers.jpg':
  1. white sneakers                       distance 0.000
  2. powder blue sneakers                 distance 0.628
  3. cream sneakers                       distance 0.635
  4. blue yellow sneakers                 distance 0.719
  5. light blue sneakers                  distance 0.728
```

Or by a sentence, matched against the reviews:

```bash
make search TEXT="great sound but the ear cushions get warm"
```

```
Closest review matches for 'great sound but the ear cushions get warm':
  1. white overear headphones             distance 1.098
  2. powderblue overear headphones        distance 1.218
  3. lilac earbuds                        distance 1.379
  4. vibrant red sneakers                 distance 1.545
  5. stylish faux leather sandals         distance 1.620
```

Smaller distance means more similar. The photo finds itself first, at 0, then other light-colored sneakers; the sentence finds the two headphones, then the earbuds. Try your own: `IMAGE=` takes any photo on your machine and `TEXT=` any sentence. To call the endpoints yourself, open http://localhost:8000/docs.

**6. Clean up.** Stop the API with Ctrl+C, then:

```bash
make clean
```

This stops the services and deletes their data. The models and the sample data stay.

To check the whole stack at once, start the services (`docker compose up -d --wait`) with the API stopped and run `make api-check`. It runs the book's curl calls, restarts the API and checks that nothing was lost.

## How much time do you have?

| Time | What to do |
|---|---|
| 15 minutes | [Run it](#run-it), steps 1 to 5. On a Mac, step 2 took 1 min 51 s and step 4 took 3 min 20 s. |
| 1 hour | The three [Try this](#try-this) experiments, then search with your own photos and sentences. |
| 1 day | [Use your own data](#use-your-own-data): load your own catalog, fix the two slow spots the experiments find, and work through [Before production](#before-production). |

## Try this

Each experiment changes one thing and measures the effect. The numbers below are from a Mac on 2026-11-21; yours will differ.

**1. Which modality finds products of the same type?** Ranks every sample product's neighbors by photo, by review text, and by both together (the two vectors joined, 50/50), and counts how often the nearest ones are the same type (sneakers, sandals, headphones, water bottles). No Docker needed.

```bash
make try-modalities
```

```
Search by                     nearest is same type  same type in top k
photo only                                    87%                 74%
review text only                              93%                 87%
photo + reviews (50/50)                      100%                 92%
```

Combining the two modalities beats either one alone on this catalog. Change the weight in `fuse()` in `experiments/modalities.py` and run it again.

**2. How many video frames does the video encoder need?** The encoder averages 8 frames. This encodes the same clip with 2 to 32 frames. No Docker needed.

```bash
make try-video-frames
```

```
frames  encode time  similarity to 8 frames  similarity to the photo
     2        0.20s                  0.9764                   0.6918
     4        0.44s                  0.9818                   0.6959
     8        1.05s                  1.0000                   0.7042
    16        2.00s                  0.9948                   0.6988
    32        3.85s                  0.9941                   0.7101
```

Time grows with the number of frames; the vector barely changes. Two frames give a vector 0.98 similar to the 8-frame one in a fifth of the time. Pass another clip with `VIDEO=`.

**3. Why does adding products take minutes?** The worker calls Milvus `flush()` after every vector it inserts. This inserts 10 vectors into a scratch collection with a flush after each one, then with one flush at the end. Needs the services: `docker compose up -d --wait`.

```bash
make try-milvus-flush
```

```
10 vectors inserted into Milvus (10 stored in the second run)
  flush after every insert (as the worker does):  105.7 s  (10.57 s per vector)
  one flush at the end:                             1.6 s
```

That flush is where most of step 4's 3 min 20 s goes. Changing `insert_features` in `src/db/milvus.py` is a good first fix.

## Use your own data

Put your products in a folder, one file per product and modality, named after the product:

```
my_products/
  images/   red_runner.jpg  blue_tote.png      .jpg .jpeg .png .webp
  reviews/  red_runner.txt  blue_tote.txt      .txt, UTF-8 (optional)
  videos/   red_runner.mp4                     .mp4 .mov .avi .webm (optional)
```

Check it first. This reads every file and sends nothing:

```bash
make check-data DIR=my_products
```

It reports each file it can't use and why: a file type it doesn't take, an image that won't open or is smaller than 32x32, an empty review or one that isn't UTF-8, a video with no readable frames, or a Git LFS pointer instead of the file. When everything passes, load it with the API running (`make serve`) and search it:

```bash
make load DIR=my_products
make search IMAGE=my_products/images/red_runner.jpg
```

Products already in the store (same name) are skipped, so you can add files and rerun. `make clean` empties the store.

## What you end up with

A running feature store with your products in it, searchable by photo or by text through an API, and three measurements of where its time and accuracy go.

Skills you'll practice:
- Encoding images, text and video into vectors with pretrained models
- Normalizing vectors so different products can be compared
- Storing vectors in Milvus and product records in PostgreSQL, and keeping them linked
- Ingesting data through an API with background jobs
- Validating input files before they reach the pipeline
- Measuring a pipeline before changing it

## Before production

This playbook runs on one machine with sample data. Before you run something like it for real:

1. **Encode outside the API.** The API encodes each product in its own process, one at a time, and answers nothing else while it does. Put the work on a queue with separate workers. *Chapter 2, "Containerization and Orchestration for Multimodal AI" (page 43); Chapter 9, "Batching and Inference Tiering" (page 344).*
2. **Batch writes to the vector database.** A flush after every insert took 105.7 s for 10 vectors, against 1.6 s for one flush at the end ([Try this 3](#try-this)). *Chapter 2, "Production Patterns for Reliability and Scale" (page 51).*
3. **Validate data where it enters.** `make check-data` checks files on your machine, but the API accepts any path it is sent. Check type, size and readability at the API too. *Chapter 4, "Validation, Transformation, Observability, and Annotation Across Modalities" (page 119).*
4. **Record which model made each vector.** Store the model name and version with every vector, so a model change means a planned re-encode instead of a mix of old and new vectors. *Chapter 8, "Data Versioning and Experiment Tracking for Multimodal AI" (page 276).*
5. **Choose the index by measuring it.** The collections use IVF_FLAT with `nlist=128` and `nprobe=10`, which is plenty for 19 products. At catalog scale, measure recall against latency before you pick an index and its settings. *Chapter 6, "Vector Databases" (page 180).*
6. **Watch ingestion and search.** Track failed jobs, encode time, search latency and shifts in the vectors over time. *Chapter 2, "Monitoring and Observability" (page 53); Chapter 8, "Observability for Multimodal Systems" (page 287).*
7. **Lock down the API.** It allows requests from any origin, has no authentication, and the Docker services use development passwords. *Chapter 11, "Protecting Data Across the Pipeline" (page 421).*
8. **Know where your data came from.** The sample photos' per-file sources weren't recorded (see [Data and licenses](#data-and-licenses)). Record source and license for every file you ingest. *Chapter 11, "Lineage and Provenance Tracking" (page 416).*

## What it costs

| Where you run it | Cost |
|---|---|
| Your machine | $0. Everything runs locally: no API keys, no paid services. About 4 GB of disk. |
| A GitHub Codespace (4 cores, 16 GB, the size this repo asks for) | Estimated $0.36 per hour at GitHub's list price (November 2026). A free personal account includes 120 core-hours a month, about 30 hours on this machine. In CI, building the container and running steps 2 to 4 took under 4 minutes. |

## How it works

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

## Run it the way the book does

These are the book's Steps 1–8 (pages 61–68), as printed apart from the fixes listed in [Differences from the printed book](#differences-from-the-printed-book). Steps 1–5 run the encoders on your laptop CPU with no other services. Steps 6–8 are optional and need Docker.

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

- `make load-samples` and `make search`: see [Run it](#run-it), steps 4 and 5. `make check-data` and `make load`: see [Use your own data](#use-your-own-data).
- `make smoke`: Steps 4–5 plus checks of the similarity claims below (about 1 minute after the first model download).
- `make api-check`: Steps 6–7 with the services running. Runs the curl calls above, restarts the API and checks that the stored vectors and job status survive.

## Tested on

| Date | OS | Python | Key libraries |
|---|---|---|---|
| 2026-10-22 | macOS 26.5.1 (arm64), Docker 28.0.1 | 3.12.15, 3.13.16 | torch 2.14.1, torchvision 0.29.1, sentence-transformers 6.2.0, fastapi 0.161.0, starlette 1.9.0, pymilvus 3.0.2, asyncpg 0.32.0, opencv-python 5.0.0, numpy 2.5.4; Milvus 3.0.3, PostgreSQL 16 |
| CI, on every push | ubuntu-latest | 3.12, 3.13 | same, from `uv.lock` (encoders); full stack with Docker on 3.12 |

## Differences from the printed book

The "First edition" column is the code and README at the `first-edition` tag, which the book describes.

| What | First edition | Now | Why |
|---|---|---|---|
| Starting the API (`uvicorn src.api.main:app --reload`, book page 67) | `uvicorn` exited with `ConnectionNotExistException: should create connection first` | Starts | Collections were created before the Milvus connection; now after it |
| Search request | `{"query_vector": [...]}` (README) returned HTTP 422 | Works | The endpoint expected a bare JSON array |
| API restart | Deleted all vectors; job status lost; unknown jobs returned HTTP 200 | Vectors and job status kept; unknown jobs return 404 | Collections were dropped on every start; job status was only in memory |
| Docker images | Milvus v2.4.0, etcd v3.5.5, `minio/minio:RELEASE.2023-03-20` | Milvus v3.0.3, etcd v3.5.25, `milvusdb/minio:RELEASE.2024-12-18`, as in Milvus's own compose file | MinIO stopped publishing Docker images in October 2025; current Milvus |
| Connection settings | Hard-coded | `DATABASE_URL`, `MILVUS_HOST`, `MILVUS_PORT`, `POSTGRES_PORT` (same defaults) | A local PostgreSQL on 5432 took the place of the Docker one |
| Clone | `git clone <repo-url>` / `cd streambuy-featurestore` (the book's tree, page 62, shows `streambuy-featurestore/`); no mention of Git LFS | Real URL and folder; Git LFS, with a light option | Without Git LFS the video test failed |
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

From my run on 2026-10-22: macOS 26.5.1 (arm64), Python 3.12.15, a light clone from GitHub, `pip install -r requirements.txt` (88 s). Python 3.13.16 gave the same numbers. This is the output of this version; it may differ from the output printed in the book, and that's okay.

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
├── CHANGELOG.md                # Changes since the first edition
├── requirements.txt            # Pinned dependencies (exported from uv.lock)
├── pyproject.toml, uv.lock     # Same dependencies for uv
├── download_models.py          # One-time model setup script
├── test_pipeline.py            # Encoder pipeline tests (no Docker needed)
├── docker-compose.yml          # PostgreSQL + Milvus infrastructure
├── schema.sql                  # Database schema
├── .env.example                # Connection settings (environment variables)
├── Makefile                    # make run, serve, load-samples, search, try-*, check-data, load, clean
├── scripts/
│   ├── load_products.py        # make load-samples, check-data, load: check files and add products
│   └── search.py               # make search: search by photo or by text
├── experiments/                # make try-*: the three Try this experiments
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
│   ├── test_own_data.py        # checks for make check-data and make load
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

If this playbook helped you, a star helps other readers find it.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2025-2026 Data Engineering for Multimodal AI. The sample images and videos are under their own licenses; see [Data and licenses](#data-and-licenses).
