# StreamBuy Multimodal Feature Store

This project builds a multimodal feature store for the fictional StreamBuy
e-commerce platform. It ingests product images, customer review text, and
product video clips, encodes each modality into dense vector embeddings,
stores them in PostgreSQL (metadata) and Milvus (vectors), and exposes a
FastAPI service for cross-modal similarity search.

## Architecture

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

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.10+** (3.11 recommended)
- **pip** (comes with Python)
- **Docker and Docker Compose** (only needed for the full-stack API, not for
  running the encoder tests)
- Approximately **4 GB of free disk space** for dependencies, pretrained
  models, and sample data

## Quick Start — Step-by-Step Playbook

Follow these steps in order. Steps 1–5 get you running the encoder pipeline
with no external services. Steps 6–8 are optional and require Docker.

### Step 1: Clone the Repository

```bash
git clone <repo-url>
cd streambuy-featurestore
```

### Step 2: Create a Virtual Environment (Recommended)

Using a virtual environment avoids conflicts with system-wide packages and
ensures PyTorch installs correctly for your platform.

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs PyTorch, torchvision, sentence-transformers, FastAPI, asyncpg,
pymilvus, and other required packages.

### Step 4: Download Pretrained Models (One-Time)

```bash
python download_models.py
```

This downloads two models into the local `models/` directory so the pipeline
runs fully offline after this step:

| Model              | Size    | Used By                |
|--------------------|---------|------------------------|
| ResNet18           | ~45 MB  | Image and video encoder|
| all-MiniLM-L6-v2   | ~80 MB  | Text/review encoder    |

**Expected output:**

```
============================================================
StreamBuy Feature Store — Model Setup
============================================================

Model directory: /path/to/streambuy-featurestore/models

[1/2] ResNet18 (image & video encoder)
  Downloading ResNet18 pretrained weights...
  Saved ResNet18 to /path/to/models/resnet18.pth (44.7 MB)

[2/2] all-MiniLM-L6-v2 (text/review encoder)
  Downloading all-MiniLM-L6-v2 sentence transformer...
  Saved all-MiniLM-L6-v2 to /path/to/models/all-MiniLM-L6-v2 (87.3 MB)

============================================================
Setup complete. All models saved locally.
The pipeline will now run fully offline.
============================================================
```

### Step 5: Run the Encoder Tests (No Docker Required)

```bash
python test_pipeline.py
```

This verifies all three encoders (image, text, video) produce correctly
shaped and normalized vectors using the sample data.

**Expected output:**

```
============================================================
StreamBuy Feature Store — Encoder Pipeline Tests
============================================================

--- Test 1: Image Encoder ---
INFO:src.encoders.image:Processing product image: .../blue_yellow_sneakers.jpg
INFO:src.encoders.image:Generated image features: shape=(512,)
[PASS] Image encoder: shape=(512,), norm=1.000000

--- Test 2: Text Encoder ---
INFO:src.encoders.text:Processing review text of length 761
INFO:src.encoders.text:Generated text features: shape=(384,)
[PASS] Text encoder: shape=(384,), norm=1.000000

--- Test 3: Video Encoder ---
INFO:src.encoders.video:Processing product video: .../white_sneakers.mp4
INFO:src.encoders.video:Generated video features: shape=(512,)
[PASS] Video encoder: shape=(512,), norm=1.000000

--- Test 4: Cross-Modal Similarity ---
  Same category (sneakers img↔vid): 0.7042
  Diff category (sneakers↔headphones): 0.5811
[PASS] Cross-modal similarity computed successfully

--- Test 5: Batch Encoding ---
  Encoded blue_yellow_sneakers.jpg
  Encoded blue_yellow_sneakers_2.jpg
  Encoded brown_leather_boots.jpg
  ... (19 images total)
[PASS] Batch encoding: 19 images encoded

  Similarity matrix (first 5 products):
              blue_yel  blue_yel  brown_le  cream_sn  faux_lea
  blue_yello    1.0000    0.8685    0.6285    0.7048    0.6611
  blue_yello    0.8685    1.0000    0.6053    0.7230    0.6066
  brown_leat    0.6285    0.6053    1.0000    0.6653    0.7159
  cream_snea    0.7048    0.7230    0.6653    1.0000    0.6041
  faux_leath    0.6611    0.6066    0.7159    0.6041    1.0000

============================================================
ALL TESTS PASSED
============================================================
```

**What to look for:**

- All five tests print `[PASS]`.
- Image and video embeddings are 512-dimensional; text embeddings are 384-dimensional.
- All vectors have unit norm (1.000000), confirming L2 normalization.
- The similarity matrix shows that similar products (e.g., two views of the
  same blue/yellow sneakers at 0.87) score higher than dissimilar products
  (e.g., sneakers vs. boots at 0.63).

### Step 6: Start the Full Stack (Optional — Requires Docker)

```bash
docker-compose up -d
```

This launches four containers:

| Service    | Port  | Purpose                        |
|------------|-------|--------------------------------|
| PostgreSQL | 5432  | Product metadata and job tracking |
| Milvus     | 19530 | Vector similarity search       |
| etcd       | 2379  | Milvus metadata store          |
| MinIO      | 9000  | Milvus object storage          |

Wait 30–60 seconds for all services to become healthy, then start the API:

```bash
uvicorn src.api.main:app --reload
```

**Expected output:**

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Connected to PostgreSQL database
INFO:     Connected to Milvus server
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 7: Try the API

Once the server is running, you can interact with the API.

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

(Use a real 512-dimensional vector from the encoder output.)

### Step 8: Shut Down

```bash
docker-compose down
deactivate                      # exit the virtual environment
```

## Extending the Code

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

## Project Structure

```
streambuy-featurestore/
├── README.md                   # This file — playbook and architecture
├── requirements.txt            # Python dependencies
├── download_models.py          # One-time model setup script
├── test_pipeline.py            # Encoder pipeline tests (no Docker needed)
├── docker-compose.yml          # PostgreSQL + Milvus infrastructure
├── schema.sql                  # Database schema
├── .gitignore                  # Excludes models/, venv/, __pycache__/
├── LICENSE                     # MIT license
├── models/                     # Pretrained weights (created by download_models.py)
│   ├── resnet18.pth
│   └── all-MiniLM-L6-v2/
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
└── sample_data/
    ├── README.md               # Data attribution and usage notes
    ├── product_images/         # 20 product photos
    ├── product_videos/         # 31 product video clips
    └── reviews/                # 18 customer review text files
```

## Encoders

| Modality | Model               | Output Dim | Notes                                    |
|----------|---------------------|------------|------------------------------------------|
| Image    | ResNet18 (ImageNet) | 512        | Classification head removed              |
| Text     | all-MiniLM-L6-v2    | 384        | Sentence-level semantic embedding        |
| Video    | ResNet18 (ImageNet) | 512        | 8 uniformly sampled frames, averaged     |

All encoders normalize output vectors to unit length for cosine similarity.

## Sample Data

See [`sample_data/README.md`](sample_data/README.md) for attribution details.
Images and videos are sourced from Unsplash and Pexels (free-use licenses).
Customer reviews are synthetically generated. The sample data exercises the
full pipeline but does not represent a production product catalog.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ImportError: ... libtorch_cpu.dylib` | Your PyTorch install is corrupted or was built for a different environment. Create a fresh virtual environment and reinstall: `pip install -r requirements.txt` |
| `AssertionError: Sample image not found` | Make sure you are running from the `streambuy-featurestore/` directory, not the parent |
| `docker-compose up` fails | Ensure Docker Desktop is running and ports 5432, 19530, 9000 are free |
| `Connection refused` on API calls | Wait for all Docker services to be healthy before starting uvicorn |

## License

MIT License. See [LICENSE](LICENSE) for details.

## Copyright

Copyright (c) 2025 Data Engineering for Multimodal AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
