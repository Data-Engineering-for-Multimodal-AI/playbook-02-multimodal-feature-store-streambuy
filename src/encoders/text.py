import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer

MODELS_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, "models"
)


class TextEncoder:
    """Encodes customer review text into feature vectors"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Load SentenceTransformer from local directory — no network calls
        model_path = os.path.normpath(
            os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
        )
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"SentenceTransformer model not found at {model_path}. "
                f"Run 'python download_models.py' first to fetch "
                f"pretrained weights."
            )

        self.model = SentenceTransformer(model_path)
        self.logger.info(f"Loaded SentenceTransformer from {model_path}")

    def encode(self, text: str) -> np.ndarray:
        """Extract 384-dim semantic embedding from review text"""
        self.logger.info(f"Processing review text of length {len(text)}")
        features = self.model.encode(text)

        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm

        self.logger.info(f"Generated text features: shape={features.shape}")
        return features
