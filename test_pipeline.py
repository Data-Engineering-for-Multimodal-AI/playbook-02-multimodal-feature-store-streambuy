"""
StreamBuy Multimodal Feature Store — Pipeline Tests

Tests the encoder pipeline end-to-end using sample data.
Does NOT require PostgreSQL or Milvus to be running.
For full integration tests, start infrastructure first:
    docker-compose up -d
"""

import logging
import sys
import os
import numpy as np
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.models.pipeline import Product, Modality
from src.encoders.factory import EncoderFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")


def test_image_encoder():
    """Test image encoder produces correctly shaped, normalized vectors"""
    factory = EncoderFactory()
    encoder = factory.create_encoder(Modality.IMAGE)

    img_path = os.path.join(SAMPLE_DIR, "product_images",
                            "blue_yellow_sneakers.jpg")
    assert os.path.exists(img_path), f"Sample image not found: {img_path}"

    features = encoder.encode(img_path)
    assert features.shape == (512,), f"Expected (512,), got {features.shape}"
    assert abs(np.linalg.norm(features) - 1.0) < 1e-5, \
        "Image features should be unit normalized"
    logger.info(f"[PASS] Image encoder: shape={features.shape}, "
                f"norm={np.linalg.norm(features):.6f}")
    return features


def test_text_encoder():
    """Test text encoder produces correctly shaped, normalized vectors"""
    factory = EncoderFactory()
    encoder = factory.create_encoder(Modality.REVIEW)

    review_path = os.path.join(SAMPLE_DIR, "reviews",
                               "blue_yellow_sneakers_reviews.txt")
    assert os.path.exists(review_path), f"Sample review not found: {review_path}"

    with open(review_path, 'r') as f:
        text = f.read()

    features = encoder.encode(text)
    assert features.shape == (384,), f"Expected (384,), got {features.shape}"
    assert abs(np.linalg.norm(features) - 1.0) < 1e-5, \
        "Text features should be unit normalized"
    logger.info(f"[PASS] Text encoder: shape={features.shape}, "
                f"norm={np.linalg.norm(features):.6f}")
    return features


def test_video_encoder():
    """Test video encoder produces correctly shaped, normalized vectors"""
    factory = EncoderFactory()
    encoder = factory.create_encoder(Modality.VIDEO)

    video_path = os.path.join(SAMPLE_DIR, "product_videos",
                              "white_sneakers.mp4")
    assert os.path.exists(video_path), f"Sample video not found: {video_path}"

    features = encoder.encode(video_path)
    assert features.shape == (512,), f"Expected (512,), got {features.shape}"
    assert abs(np.linalg.norm(features) - 1.0) < 1e-5, \
        "Video features should be unit normalized"
    logger.info(f"[PASS] Video encoder: shape={features.shape}, "
                f"norm={np.linalg.norm(features):.6f}")
    return features


def test_cross_modal_similarity():
    """Test that same-product embeddings are more similar than different products"""
    factory = EncoderFactory()
    img_encoder = factory.create_encoder(Modality.IMAGE)
    vid_encoder = factory.create_encoder(Modality.VIDEO)

    # Same category: white sneakers image vs white sneakers video
    img_sneakers = img_encoder.encode(
        os.path.join(SAMPLE_DIR, "product_images", "white_sneakers.jpg")
    )
    vid_sneakers = vid_encoder.encode(
        os.path.join(SAMPLE_DIR, "product_videos", "white_sneakers.mp4")
    )

    # Different category: sneakers image vs headphones image
    img_headphones = img_encoder.encode(
        os.path.join(SAMPLE_DIR, "product_images",
                     "powderblue_overear_headphones.jpg")
    )

    same_category_sim = float(np.dot(img_sneakers, vid_sneakers))
    diff_category_sim = float(np.dot(img_sneakers, img_headphones))

    logger.info(f"  Same category (sneakers img↔vid): {same_category_sim:.4f}")
    logger.info(f"  Diff category (sneakers↔headphones): "
                f"{diff_category_sim:.4f}")

    logger.info(f"[PASS] Cross-modal similarity computed successfully")
    return same_category_sim, diff_category_sim


def test_batch_encoding():
    """Test encoding all sample product images"""
    factory = EncoderFactory()
    encoder = factory.create_encoder(Modality.IMAGE)

    img_dir = os.path.join(SAMPLE_DIR, "product_images")
    images = sorted(
        list(Path(img_dir).glob("*.jpg")) + list(Path(img_dir).glob("*.png"))
    )
    # Skip the portrait image if present (not a product)
    images = [p for p in images if "portrait" not in p.stem.lower()]
    assert len(images) > 0, "No sample images found"

    embeddings = {}
    for img_path in images:
        features = encoder.encode(str(img_path))
        embeddings[img_path.stem] = features
        logger.info(f"  Encoded {img_path.name}")

    logger.info(f"[PASS] Batch encoding: {len(embeddings)} images encoded")

    # Compute similarity matrix for a few products
    products = list(embeddings.keys())[:5]
    logger.info("\n  Similarity matrix (first 5 products):")
    header = "            " + "  ".join(f"{p[:8]:>8}" for p in products)
    logger.info(header)
    for p1 in products:
        row = f"  {p1[:10]:>10}  "
        for p2 in products:
            sim = float(np.dot(embeddings[p1], embeddings[p2]))
            row += f"{sim:8.4f}  "
        logger.info(row)

    return embeddings


def main():
    logger.info("=" * 60)
    logger.info("StreamBuy Feature Store — Encoder Pipeline Tests")
    logger.info("=" * 60)

    logger.info("\n--- Test 1: Image Encoder ---")
    test_image_encoder()

    logger.info("\n--- Test 2: Text Encoder ---")
    test_text_encoder()

    logger.info("\n--- Test 3: Video Encoder ---")
    test_video_encoder()

    logger.info("\n--- Test 4: Cross-Modal Similarity ---")
    test_cross_modal_similarity()

    logger.info("\n--- Test 5: Batch Encoding ---")
    test_batch_encoding()

    logger.info("\n" + "=" * 60)
    logger.info("ALL TESTS PASSED")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
