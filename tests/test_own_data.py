"""Checks for the "Use your own data" loader (scripts/load_products.py). No Docker."""

import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from load_products import scan  # noqa: E402

SAMPLES = ROOT / "sample_data"


def test_samples_pass_and_pair_photos_with_reviews():
    products, problems = scan(SAMPLES, samples=True)
    assert problems == []
    assert len(products) == 19
    assert all(set(f) == {"image", "review"} for f in products.values())
    assert products["blue_yellow_sneakers_2"]["review"].name == "blue_yellow_sneakers_reviews.txt"


def test_good_folder(tmp_path):
    (tmp_path / "images").mkdir()
    (tmp_path / "reviews").mkdir()
    shutil.copy(SAMPLES / "product_images" / "white_sneakers.jpg", tmp_path / "images" / "court.jpg")
    (tmp_path / "reviews" / "court.txt").write_text("Comfortable all day.", encoding="utf-8")
    (tmp_path / "images" / ".DS_Store").write_bytes(b"\0")
    products, problems = scan(tmp_path)
    assert problems == []
    assert set(products) == {"court"}
    assert set(products["court"]) == {"image", "review"}


@pytest.mark.parametrize("name,content,expected", [
    ("images/broken.jpg", b"not an image", "can't open as an image"),
    ("images/notes.gif", b"GIF89a", "not an image file type"),
    ("reviews/empty.txt", b"", "empty file"),
    ("reviews/latin1.txt", b"\xff\xfe\x00bad", "not UTF-8 text"),
    ("videos/clip.mp4", b"version https://git-lfs.github.com/spec/v1\n", "Git LFS pointer"),
    ("videos/fake.mp4", b"not a video", "no readable video frames"),
])
def test_bad_files_are_reported(tmp_path, name, content, expected):
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    _, problems = scan(tmp_path)
    assert len(problems) == 1 and expected in problems[0], problems


def test_tiny_image_is_reported(tmp_path):
    (tmp_path / "images").mkdir()
    Image.new("RGB", (16, 16)).save(tmp_path / "images" / "tiny.png")
    _, problems = scan(tmp_path)
    assert problems == ["images/tiny.png: too small (16x16), needs at least 32x32"]
