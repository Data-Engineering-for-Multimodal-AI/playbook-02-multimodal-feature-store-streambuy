"""Try this 3: why does adding products take minutes? (make try-milvus-flush)

The worker (src/db/milvus.py, insert_features) calls flush() after every
vector it inserts, so each product waits for Milvus to seal and persist a
segment. make load-samples writes 38 vectors (19 photos and 19 reviews).
This inserts 10 vectors into a scratch collection two ways: flush after each
insert, and one flush at the end. Then it drops the collection.

Needs Milvus running: docker compose up -d --wait
"""

import os
import time

import numpy as np
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

N, DIM, NAME = 10, 512, "streambuy_try_flush"


def fresh_collection():
    if utility.has_collection(NAME):
        utility.drop_collection(NAME)
    schema = CollectionSchema([
        FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("product_id", DataType.INT64),
        FieldSchema("vector", DataType.FLOAT_VECTOR, dim=DIM),
    ])
    return Collection(NAME, schema)


def main():
    connections.connect(host=os.environ.get("MILVUS_HOST", "localhost"),
                        port=os.environ.get("MILVUS_PORT", "19530"))
    rng = np.random.default_rng(0)
    vecs = rng.normal(size=(N, DIM)).astype("float32")
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)

    col = fresh_collection()
    start = time.time()
    for i, v in enumerate(vecs):
        col.insert([[i], [v.tolist()]])
        col.flush()
    each = time.time() - start

    col = fresh_collection()
    start = time.time()
    for i, v in enumerate(vecs):
        col.insert([[i], [v.tolist()]])
    col.flush()
    once = time.time() - start
    count = col.num_entities
    utility.drop_collection(NAME)

    print(f"{N} vectors inserted into Milvus ({count} stored in the second run)")
    print(f"  flush after every insert (as the worker does): {each:6.1f} s  ({each / N:.2f} s per vector)")
    print(f"  one flush at the end:                          {once:6.1f} s")


if __name__ == "__main__":
    main()
