import logging
import numpy as np
from typing import Dict, Any
from ..models.pipeline import (
    Product, ProcessingJob, ProcessingResult,
    Modality, FeatureStatus
)
from ..encoders.factory import EncoderFactory
from ..db.postgres import PostgresClient
from ..db.milvus import MilvusClient


class FeatureProcessor:
    """Processes StreamBuy products and extracts multimodal features"""

    # Embedding dimensions per modality
    DIMENSIONS = {
        Modality.IMAGE: 512,    # ResNet18 features
        Modality.VIDEO: 512,    # Averaged ResNet18 frame features
        Modality.REVIEW: 384,   # MiniLM sentence embedding
    }

    def __init__(self, pg_client: PostgresClient,
                 milvus_client: MilvusClient):
        self.logger = logging.getLogger(__name__)
        self.pg_client = pg_client
        self.milvus_client = milvus_client
        self.encoder_factory = EncoderFactory()

    def create_collections(self):
        """Create vector collections — one per modality.

        Needs a Milvus connection, so call it after milvus_client.connect().
        """
        for modality, dim in self.DIMENSIONS.items():
            self.milvus_client.create_collection(modality, dim)

    async def process_product(self, product: Product,
                               job_id: int) -> Dict[str, Any]:
        """Extract features from all available modalities"""
        try:
            await self.pg_client.update_job_status(
                job_id, FeatureStatus.PROCESSING
            )
            results = []

            modality_map = {
                Modality.IMAGE: product.data_paths.get("image"),
                Modality.VIDEO: product.data_paths.get("video"),
                Modality.REVIEW: product.data_paths.get("review"),
            }

            for modality, data_path in modality_map.items():
                if not data_path:
                    continue

                encoder = self.encoder_factory.create_encoder(modality)

                if modality == Modality.REVIEW:
                    with open(data_path, 'r') as f:
                        features = encoder.encode(f.read())
                else:
                    features = encoder.encode(data_path)

                result = ProcessingResult(
                    job_id=job_id,
                    product_id=int(product.id) if product.id else None,
                    modality=modality.value,
                    status="processed",
                )
                # Store vector as list for PostgreSQL
                result.feature_vector = features.tolist()
                results.append(result)

                self.milvus_client.insert_features(
                    modality, int(product.id), features
                )

            for result in results:
                await self.pg_client.save_result(result)

            await self.pg_client.update_job_status(
                job_id, FeatureStatus.PROCESSED
            )
            return {
                "status": "success",
                "job_id": job_id,
                "modalities_processed": len(results)
            }

        except Exception as e:
            self.logger.error(
                f"Error processing product {product.id}: {str(e)}"
            )
            await self.pg_client.update_job_status(
                job_id, FeatureStatus.FAILED
            )
            return {"status": "error", "job_id": job_id, "error": str(e)}
