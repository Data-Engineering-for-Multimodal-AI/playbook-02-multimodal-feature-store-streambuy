import logging
import numpy as np
from typing import List, Optional
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)
from ..models.pipeline import Modality


class MilvusClient:
    """Client for Milvus vector database operations"""

    def __init__(self, host: str = "localhost", port: int = 19530):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.collections = {}

    def connect(self):
        """Connect to Milvus server"""
        connections.connect(host=self.host, port=self.port)
        self.logger.info("Connected to Milvus server")

    def disconnect(self):
        """Disconnect from Milvus server"""
        connections.disconnect("default")
        self.logger.info("Disconnected from Milvus server")

    def create_collection(self, modality: Modality, dim: int):
        """Create a collection for a specific modality with IVF index"""
        if modality in self.collections:
            return

        collection_name = f"streambuy_{modality.value}_features"

        # Reuse an existing collection, so restarting the API keeps the stored
        # vectors (PostgreSQL keeps its rows too). To start from scratch, remove
        # the Docker volumes: docker compose down -v
        if utility.has_collection(collection_name):
            self.collections[modality] = Collection(name=collection_name)
            self.logger.info(f"Using existing collection: {collection_name}")
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64,
                        is_primary=True, auto_id=True),
            FieldSchema(name="product_id", dtype=DataType.INT64),
            FieldSchema(name="feature_vector",
                        dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        schema = CollectionSchema(
            fields=fields,
            description=f"StreamBuy {modality.value} feature vectors"
        )
        collection = Collection(name=collection_name, schema=schema)

        # IVF_FLAT index — partitions vectors into clusters
        # nlist=128 for small datasets, increase to 1024+ in production
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(
            field_name="feature_vector",
            index_params=index_params
        )
        self.collections[modality] = collection
        self.logger.info(f"Created collection: {collection_name} (dim={dim})")

    def insert_features(self, modality: Modality,
                         product_id: int,
                         feature_vector: np.ndarray):
        """Insert feature vector into the appropriate collection"""
        collection = self.collections[modality]
        entities = [[product_id], [feature_vector.tolist()]]
        collection.insert(entities)
        collection.flush()
        self.logger.info(
            f"Inserted {modality.value} features for product {product_id}"
        )

    def search_similar(self, modality: Modality,
                        query_vector: np.ndarray,
                        limit: int = 10) -> List[tuple]:
        """Search for similar products by feature vector"""
        collection = self.collections[modality]
        collection.load()

        # nprobe=10 searches the 10 nearest clusters
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        results = collection.search(
            data=[query_vector.tolist()],
            anns_field="feature_vector",
            param=search_params,
            limit=limit,
            output_fields=["product_id"]
        )
        return [
            (hit.entity.get("product_id"), hit.distance)
            for hit in results[0]
        ]
