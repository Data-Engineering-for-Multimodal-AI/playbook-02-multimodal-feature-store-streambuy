"""Try this 1: which modality finds products of the same kind? (make try-modalities)

Encodes the 18 sample products that have both a photo and reviews, then for
each one ranks all the others by photo, by review text, and by both together.
It counts how often the closest other products are the same type (sneakers,
sandals, headphones, water bottles). Ranking uses L2 distance between unit vectors, the
same metric the Milvus collections use. No Docker needed.

Change MODALITIES_TO_FUSE or the weights in fuse() and run it again.
"""

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.encoders.factory import EncoderFactory  # noqa: E402
from src.models.pipeline import Modality  # noqa: E402

# Product types, from the file names. Types with only one product (boots, earbuds,
# backpack) stay in the catalog as distractors but aren't scored, since nothing
# else of their type exists to find.
TYPES = ["sneakers", "sandals", "boots", "headphones", "earbuds", "backpack", "waterbottle"]


def fuse(image_vec, review_vec, w_image=0.5):
    """Weighted concatenation, renormalized to length 1."""
    v = np.concatenate([np.sqrt(w_image) * image_vec, np.sqrt(1 - w_image) * review_vec])
    return v / np.linalg.norm(v)


def hit_rates(vectors, labels):
    """For each scored product: is its nearest other product the same type, and
    how many of its k nearest are, where k is the number of others of its type."""
    d = np.linalg.norm(vectors[:, None, :] - vectors[None, :, :], axis=-1)
    np.fill_diagonal(d, np.inf)
    order = np.argsort(d, axis=1)
    scored = [i for i in range(len(labels)) if labels.count(labels[i]) > 1]
    top1 = np.mean([labels[order[i][0]] == labels[i] for i in scored])
    recall = np.mean([np.mean([labels[j] == labels[i] for j in order[i][:labels.count(labels[i]) - 1]])
                      for i in scored])
    return top1, recall, len(scored)


def main():
    products = []
    for image in sorted((ROOT / "sample_data" / "product_images").iterdir()):
        review = ROOT / "sample_data" / "reviews" / f"{image.stem}_reviews.txt"
        if review.exists():
            kind = next(t for t in TYPES if t in image.stem)
            products.append((image, review, kind))

    factory = EncoderFactory()
    image_enc = factory.create_encoder(Modality.IMAGE)
    text_enc = factory.create_encoder(Modality.REVIEW)
    start = time.time()
    img = np.stack([image_enc.encode(str(p[0])) for p in products])
    txt = np.stack([text_enc.encode(p[1].read_text()) for p in products])
    labels = [p[2] for p in products]
    print(f"Encoded {len(products)} products (photo + reviews) in {time.time() - start:.1f} s\n")

    print(f"{'Search by':28} {'nearest is same type':>21} {'same type in top k':>19}")
    rows = [("photo only", img), ("review text only", txt),
            ("photo + reviews (50/50)", np.stack([fuse(a, b) for a, b in zip(img, txt)]))]
    for name, vecs in rows:
        t1, rk, n = hit_rates(vecs, labels)
        print(f"{name:28} {t1:>20.0%} {rk:>19.0%}")
    kinds = {k: labels.count(k) for k in TYPES if k in labels}
    print(f"\nScored {n} products. Products per type: {kinds}")
    print("k is the number of other products of the same type.")


if __name__ == "__main__":
    main()
