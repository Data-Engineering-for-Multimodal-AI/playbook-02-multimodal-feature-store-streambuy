import logging
from ..models.pipeline import Modality
from .image import ImageEncoder
from .text import TextEncoder
from .video import VideoEncoder


class EncoderFactory:
    """Factory for creating encoders based on modality"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encoders = {}

    def create_encoder(self, modality: Modality):
        """Create or retrieve a cached encoder for a specific modality"""
        if modality not in self.encoders:
            self.logger.info(f"Creating encoder for {modality.value}")
            if modality == Modality.REVIEW:
                self.encoders[modality] = TextEncoder()
            elif modality == Modality.IMAGE:
                self.encoders[modality] = ImageEncoder()
            elif modality == Modality.VIDEO:
                self.encoders[modality] = VideoEncoder()
            else:
                raise ValueError(f"Unsupported modality: {modality}")

        return self.encoders[modality]
