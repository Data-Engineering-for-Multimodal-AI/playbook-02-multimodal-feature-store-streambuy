"""Search the running feature store by photo or by text (make search).

    python scripts/search.py --image sample_data/product_images/white_sneakers.jpg
    python scripts/search.py --text "light and comfortable for long walks"

The query is encoded with the same model the store used (ResNet18 for photos,
MiniLM for review text), sent to POST /search/{modality}, and the product IDs
in the answer are looked up in PostgreSQL to print their names. Distance is
L2 between unit vectors: 0 is identical, and smaller is more similar.
"""

import argparse
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.encoders.factory import EncoderFactory  # noqa: E402
from src.models.pipeline import Modality  # noqa: E402

API = os.environ.get("API_URL", "http://localhost:8000")
DSN = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/streambuy_features")


async def names(ids):
    conn = await asyncpg.connect(DSN)
    try:
        rows = await conn.fetch("SELECT id, name FROM products WHERE id = ANY($1)", ids)
        return {r["id"]: r["name"] for r in rows}
    finally:
        await conn.close()


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    q = p.add_mutually_exclusive_group(required=True)
    q.add_argument("--image", help="path to a product photo (yours or a sample)")
    q.add_argument("--text", help="a sentence to match against product reviews")
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args()

    modality = Modality.IMAGE if args.image else Modality.REVIEW
    query = args.image or args.text
    if args.image and not Path(args.image).is_file():
        sys.exit(f"No such file: {args.image}")
    vector = EncoderFactory().create_encoder(modality).encode(query)

    body = json.dumps({"query_vector": vector.tolist()}).encode()
    req = urllib.request.Request(f"{API}/search/{modality.value}?limit={args.limit}",
                                 data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            hits = json.loads(resp.read())
    except OSError:
        sys.exit(f"The API isn't answering at {API}. Start it first with: make serve")
    if not hits:
        sys.exit("No products in the store yet. Add some with: make load-samples")

    found = asyncio.run(names([h["product_id"] for h in hits]))
    print(f"Closest {modality.value} matches for {query!r}:")
    for rank, h in enumerate(hits, 1):
        print(f"  {rank}. {found.get(h['product_id'], h['product_id']):36} distance {h['distance']:.3f}")


if __name__ == "__main__":
    main()
