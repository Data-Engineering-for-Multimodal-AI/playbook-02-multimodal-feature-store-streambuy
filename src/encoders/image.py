import logging
import os
import numpy as np
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

MODELS_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, "models"
)


class ImageEncoder:
    """Encodes product images into feature vectors"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Load ResNet18 from local weights — no network calls
        weights_path = os.path.normpath(
            os.path.join(MODELS_DIR, "resnet18.pth")
        )
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"ResNet18 weights not found at {weights_path}. "
                f"Run 'python download_models.py' first to fetch "
                f"pretrained weights."
            )

        base_model = models.resnet18(weights=None)
        base_model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        self.logger.info(f"Loaded ResNet18 weights from {weights_path}")

        # Remove classification head, keep feature extraction layers
        self.model = torch.nn.Sequential(*(list(base_model.children())[:-1]))
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def encode(self, image_path: str) -> np.ndarray:
        """Extract 512-dim feature vector from a product image"""
        self.logger.info(f"Processing product image: {image_path}")
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0)

        with torch.no_grad():
            features = self.model(image_tensor)
            features = features.squeeze().numpy()

        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm

        self.logger.info(f"Generated image features: shape={features.shape}")
        return features
