import logging
import asyncio
from typing import Dict, Any
from .tasks import FeatureProcessor
from ..db.postgres import PostgresClient
from ..db.milvus import MilvusClient
from ..models.pipeline import Product, ProcessingJob


class TaskManager:
    """Manages background processing tasks"""

    def __init__(self, pg_client: PostgresClient,
                 milvus_client: MilvusClient):
        self.logger = logging.getLogger(__name__)
        self.processor = FeatureProcessor(pg_client, milvus_client)
        self.tasks: Dict[str, asyncio.Task] = {}

    async def submit_job(self, product: Product,
                          job: ProcessingJob) -> Dict[str, Any]:
        """Submit a new feature processing job"""
        job_key = job.job_id or str(job.product_id)
        if job_key in self.tasks:
            return {"status": "error", "message": "Job already exists"}

        task = asyncio.create_task(
            self.processor.process_product(product, int(job_key))
        )
        self.tasks[job_key] = task
        return {"status": "submitted", "job_id": job_key}

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a processing job"""
        if job_id not in self.tasks:
            return {"status": "error", "message": "Job not found"}

        task = self.tasks[job_id]
        if task.done():
            try:
                return task.result()
            except Exception as e:
                return {"status": "error", "job_id": job_id,
                        "error": str(e)}
        return {"status": "processing", "job_id": job_id}
