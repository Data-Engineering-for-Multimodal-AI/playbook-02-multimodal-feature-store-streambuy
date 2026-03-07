from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class Modality(str, Enum):
    """StreamBuy product data modalities"""
    REVIEW = "review"       # Customer review text
    IMAGE = "image"         # Product photos
    VIDEO = "video"         # Product demo clips


class FeatureStatus(str, Enum):
    """Status of feature processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Product(BaseModel):
    """StreamBuy product metadata"""
    id: Optional[str] = None
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    data_paths: Dict[str, str] = {}
    created_at: datetime = None
    updated_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class ProcessingJob(BaseModel):
    """Job for processing product features"""
    job_id: Optional[str] = None
    product_id: str
    modalities: List[str] = []
    status: str = "pending"
    created_at: datetime = None
    updated_at: datetime = None
    error_message: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class ProcessingResult(BaseModel):
    """Result of processing product features"""
    job_id: int
    product_id: Optional[int] = None
    modality: str
    status: str = "processed"
    feature_id: Optional[str] = None
    feature_vector: Optional[List[float]] = None
    error_message: Optional[str] = None
