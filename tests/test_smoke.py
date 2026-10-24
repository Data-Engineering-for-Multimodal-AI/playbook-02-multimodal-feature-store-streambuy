"""
Smoke test for the encoder playbook (Steps 4-5): CPU only, no Docker.

Needs the models (python download_models.py) and the one sample video the tests
use (git lfs pull --include="sample_data/product_videos/white_sneakers.mp4").
Run with `make smoke`. The full-stack API check (Steps 6-7) is tests/api_check.sh.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import test_pipeline  # noqa: E402


def test_printed_command_passes():
    """python test_pipeline.py, as printed, exits 0 and prints ALL TESTS PASSED"""
    result = subprocess.run([sys.executable, "test_pipeline.py"], cwd=ROOT,
                            capture_output=True, text=True, timeout=600)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output[-3000:]
    assert "ALL TESTS PASSED" in output
    assert "[PASS] Batch encoding: 19 images encoded" in output


def test_same_product_more_similar_than_different():
    """Test 4's docstring claim, which test_pipeline.py prints but doesn't check"""
    same, different = test_pipeline.test_cross_modal_similarity()
    assert same > different


def test_readme_similarity_claim():
    """README: two views of the blue/yellow sneakers (0.87) score higher than sneakers vs boots (0.63)"""
    embeddings = test_pipeline.test_batch_encoding()
    a = embeddings["blue_yellow_sneakers"]
    assert float(a @ embeddings["blue_yellow_sneakers_2"]) > float(a @ embeddings["brown_leather_boots"])
