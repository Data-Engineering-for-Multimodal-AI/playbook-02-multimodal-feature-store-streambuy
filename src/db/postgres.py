import logging
import json
import asyncpg
from typing import Optional, List
from ..models.pipeline import Product, ProcessingJob, ProcessingResult, FeatureStatus


class PostgresClient:
    """Client for PostgreSQL database operations"""

    def __init__(self, dsn: str):
        self.logger = logging.getLogger(__name__)
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.dsn)
        self.logger.info("Connected to PostgreSQL database")

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("Closed PostgreSQL connection")

    async def create_product(self, product: Product) -> int:
        """Create a new product record"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO products (name, category, brand, price)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """
            product_id = await conn.fetchval(
                query,
                product.name,
                product.category,
                product.brand,
                product.price
            )
            self.logger.info(f"Created product record with ID: {product_id}")
            return product_id

    async def create_job(self, job: ProcessingJob) -> int:
        """Create a new processing job"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO processing_jobs (product_id, status, created_at)
                VALUES ($1, $2, NOW())
                RETURNING id
            """
            job_id = await conn.fetchval(
                query,
                int(job.product_id),
                job.status
            )
            self.logger.info(f"Created processing job with ID: {job_id}")
            return job_id

    async def update_job_status(self, job_id: int, status: FeatureStatus):
        """Update job status"""
        async with self.pool.acquire() as conn:
            query = """
                UPDATE processing_jobs
                SET status = $1, updated_at = NOW()
                WHERE id = $2
            """
            await conn.execute(query, status.value, job_id)
            self.logger.info(f"Updated job {job_id} status to {status.value}")

    async def save_result(self, result: ProcessingResult):
        """Save processing result"""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO processing_results
                (job_id, modality, feature_vector, created_at)
                VALUES ($1, $2, $3, NOW())
            """
            await conn.execute(
                query,
                result.job_id,
                result.modality,
                result.feature_vector
            )
            self.logger.info(f"Saved result for job {result.job_id}")

    async def get_product_results(self, product_id: int) -> List[dict]:
        """Get all processing results for a product"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT pr.id, pr.job_id, pr.modality, pr.created_at
                FROM processing_results pr
                JOIN processing_jobs pj ON pr.job_id = pj.id
                WHERE pj.product_id = $1
                ORDER BY pr.created_at DESC
            """
            rows = await conn.fetch(query, product_id)
            return [dict(row) for row in rows]
