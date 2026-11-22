"""Add the 19 sample products to the running API (make load-samples).

Each product is sent to POST /products/ with its photo and, when there is one,
its reviews, the same request the book's curl example makes. The API encodes
them in the background; this script waits until every job has finished.
Products that are already in the database are skipped, so it is safe to rerun.

Needs the API running (make serve) and DATABASE_URL if PostgreSQL isn't on 5432.
"""

import asyncio
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import asyncpg

API = os.environ.get("API_URL", "http://localhost:8000")
DSN = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/streambuy_features")
ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "sample_data" / "product_images"
REVIEWS = ROOT / "sample_data" / "reviews"
CATEGORIES = {"sneakers": "footwear", "boots": "footwear", "sandals": "footwear",
              "headphones": "audio", "earbuds": "audio", "backpack": "bags",
              "waterbottle": "drinkware"}


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


async def existing_names():
    conn = await asyncpg.connect(DSN)
    try:
        return {r["name"] for r in await conn.fetch("SELECT name FROM products")}
    finally:
        await conn.close()


def main():
    try:
        call("GET", "/openapi.json")
    except OSError:
        sys.exit(f"The API isn't answering at {API}. Start it first with: make serve")

    have = asyncio.run(existing_names())
    start = time.time()
    jobs = []
    for image in sorted(IMAGES.iterdir()):
        if image.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        stem = image.stem
        name = stem.replace("_", " ")
        if name in have:
            continue
        review = REVIEWS / f"{stem.removesuffix('_2')}_reviews.txt"
        paths = {"image": str(image.relative_to(ROOT))}
        if review.exists():
            paths["review"] = str(review.relative_to(ROOT))
        category = next((c for k, c in CATEGORIES.items() if k in stem), None)
        job = call("POST", "/products/", {"name": name, "category": category,
                                         "brand": "StreamBuy", "data_paths": paths})
        jobs.append((name, job["job_id"], list(paths)))

    if not jobs:
        print(f"All {len(have)} sample products are already loaded.")
        return

    for name, job_id, modalities in jobs:
        while True:
            status = call("GET", f"/jobs/{job_id}")["status"]
            if status not in ("pending", "processing"):
                break
            time.sleep(0.5)
        print(f"  {status:8} {name:36} {' + '.join(modalities)}")
    print(f"Added {len(jobs)} products in {time.time() - start:.0f} s.")


if __name__ == "__main__":
    main()
