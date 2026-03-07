"""
StreamBuy Feature Store — One-Time Model Setup

Downloads pretrained model weights and saves them to the local models/
directory so the pipeline runs fully offline with no network dependency.

Usage:
    python download_models.py

Models downloaded:
    - ResNet18 (~45 MB) — used by image and video encoders
    - all-MiniLM-L6-v2 (~80 MB) — used by the text/review encoder

After running this script, all encoders load weights from models/ and
never attempt network downloads.
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def download_resnet18():
    """Download ResNet18 weights and save as a PyTorch state dict"""
    import torch
    import torchvision.models as models

    save_path = os.path.join(MODELS_DIR, "resnet18.pth")
    if os.path.exists(save_path):
        logger.info(f"  ResNet18 already exists at {save_path} — skipping")
        return

    logger.info("  Downloading ResNet18 pretrained weights...")
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
    torch.save(model.state_dict(), save_path)

    size_mb = os.path.getsize(save_path) / (1024 * 1024)
    logger.info(f"  Saved ResNet18 to {save_path} ({size_mb:.1f} MB)")


def download_sentence_transformer():
    """Download all-MiniLM-L6-v2 and save to a local directory"""
    from sentence_transformers import SentenceTransformer

    save_path = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
    if os.path.exists(save_path) and os.listdir(save_path):
        logger.info(f"  all-MiniLM-L6-v2 already exists at {save_path} — skipping")
        return

    logger.info("  Downloading all-MiniLM-L6-v2 sentence transformer...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    model.save(save_path)

    # Calculate directory size
    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, filenames in os.walk(save_path)
        for f in filenames
    )
    size_mb = total / (1024 * 1024)
    logger.info(f"  Saved all-MiniLM-L6-v2 to {save_path} ({size_mb:.1f} MB)")


def main():
    logger.info("=" * 60)
    logger.info("StreamBuy Feature Store — Model Setup")
    logger.info("=" * 60)

    os.makedirs(MODELS_DIR, exist_ok=True)
    logger.info(f"\nModel directory: {MODELS_DIR}\n")

    logger.info("[1/2] ResNet18 (image & video encoder)")
    try:
        download_resnet18()
    except Exception as e:
        logger.error(f"  FAILED: {e}")
        logger.error("  Make sure you have internet access and torch installed.")
        sys.exit(1)

    logger.info("\n[2/2] all-MiniLM-L6-v2 (text/review encoder)")
    try:
        download_sentence_transformer()
    except Exception as e:
        logger.error(f"  FAILED: {e}")
        logger.error("  Make sure you have internet access and "
                      "sentence-transformers installed.")
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("Setup complete. All models saved locally.")
    logger.info("The pipeline will now run fully offline.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
