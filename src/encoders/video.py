import logging
import os
import numpy as np
import torch
import torchvision.transforms as transforms
import torchvision.models as models
import cv2

MODELS_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, "models"
)


class VideoEncoder:
    """Encodes product video clips into feature vectors"""

    def __init__(self, sample_frames=8):
        self.logger = logging.getLogger(__name__)
        self.sample_frames = sample_frames

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
            transforms.ToPILImage(),
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def encode(self, video_path: str) -> np.ndarray:
        """Extract 512-dim feature vector by averaging sampled frame features"""
        self.logger.info(f"Processing product video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames <= 0:
            cap.release()
            # A clone without Git LFS has small text pointer files instead of videos
            with open(video_path, "rb") as f:
                if f.read(40).startswith(b"version https://git-lfs"):
                    raise ValueError(
                        f"{video_path} is a Git LFS pointer, not a video. "
                        "Install Git LFS and run: git lfs pull --include=\"" + video_path + "\""
                    )
            raise ValueError(f"Could not read video frames from {video_path}")

        frame_indices = np.linspace(
            0, total_frames - 1, self.sample_frames, dtype=int
        )

        frame_features = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = self.transform(frame_rgb).unsqueeze(0)

            with torch.no_grad():
                feat = self.model(tensor).squeeze().numpy()
            frame_features.append(feat)

        cap.release()

        if len(frame_features) == 0:
            raise ValueError(f"No frames could be extracted from {video_path}")

        # Average frame features into a single product-level embedding
        features = np.mean(frame_features, axis=0)
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm

        self.logger.info(f"Generated video features: shape={features.shape}")
        return features
