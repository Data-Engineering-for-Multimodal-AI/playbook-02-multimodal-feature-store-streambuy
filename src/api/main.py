import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from ..models.pipeline import Product, ProcessingJob, Modality
from ..db.postgres import PostgresClient
from ..db.milvus import MilvusClient
from ..worker.manager import TaskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients. Connection settings come from environment variables
# (see .env.example); the defaults match docker-compose.yml.
pg_client = PostgresClient(
    os.environ.get("DATABASE_URL",
                   "postgresql://user:password@localhost:5432/streambuy_features")
)
milvus_client = MilvusClient(
    host=os.environ.get("MILVUS_HOST", "localhost"),
    port=int(os.environ.get("MILVUS_PORT", "19530")),
)
task_manager = TaskManager(pg_client, milvus_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connections across app lifecycle"""
    await pg_client.connect()
    milvus_client.connect()
    yield
    await pg_client.close()
    milvus_client.disconnect()


app = FastAPI(
    title="StreamBuy Multimodal Feature Store",
    description="API for storing and retrieving multimodal product features",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/products/", response_model=ProcessingJob)
async def create_product(product: Product,
                          background_tasks: BackgroundTasks):
    """Ingest a new product and start feature extraction"""
    try:
        product_id = await pg_client.create_product(product)
        product.id = str(product_id)

        job = ProcessingJob(
            job_id=str(product_id),
            product_id=str(product_id),
            modalities=list(product.data_paths.keys())
        )
        job_id = await pg_client.create_job(job)
        job.job_id = str(job_id)

        background_tasks.add_task(
            task_manager.submit_job, product, job
        )
        return job

    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of a feature processing job"""
    try:
        return await task_manager.get_job_status(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}/features")
async def get_product_features(product_id: int):
    """Get all extracted features for a product"""
    try:
        return await pg_client.get_product_results(product_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/{modality}")
async def search_similar(modality: Modality,
                          query_vector: List[float],
                          limit: int = 10):
    """Search for visually or semantically similar products"""
    try:
        import numpy as np
        results = milvus_client.search_similar(
            modality, np.array(query_vector), limit
        )
        return [
            {"product_id": pid, "distance": dist}
            for pid, dist in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
